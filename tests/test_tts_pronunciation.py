from pathlib import Path
from types import SimpleNamespace

from videotrans.task import _stage_dubbing
from videotrans.task._base import BaseTask
from videotrans.task._stage_dubbing import DubbingMixin
from videotrans.tts._base import BaseTTS
from videotrans.tts import _openaitts
from videotrans.tts._openaitts import OPENAITTS
from videotrans.tts.pronunciation import (
    BENCHMARK_FIXTURES,
    prepare_tts_text,
)
from videotrans.util.help_misc import get_md5


def test_prepare_tts_text_keeps_input_and_is_vietnamese_only():
    original = "ChatGPT dùng API và AI."

    spoken = prepare_tts_text(original, language="vi")

    assert original == "ChatGPT dùng API và AI."
    assert spoken == "Chát Gi Pi Ti dùng ây pi ai và ây ai."
    assert prepare_tts_text(original, language="en") == original
    assert prepare_tts_text(original, language="zh-cn") == original


def test_project_glossary_overrides_builtin_and_longest_term_wins(tmp_path):
    (tmp_path / "tts-glossary.txt").write_text(
        "AI=ai-project\nOpenRouter=open-router-project\n",
        encoding="utf-8",
    )

    spoken = prepare_tts_text(
        "OpenRouter AI API",
        language="vi-VN",
        project_dir=tmp_path,
        glossary={"API": "api-explicit", "OpenRouter AI": "phrase-explicit"},
    )

    assert spoken == "phrase-explicit api-explicit"


def test_project_glossary_duplicate_last_line_wins(tmp_path):
    (tmp_path / "tts-glossary.txt").write_text(
        "GitHub=first\ngithub=second\n",
        encoding="utf-8",
    )

    assert prepare_tts_text("GitHub", language="vi", project_dir=tmp_path) == "second"


def test_base_tts_consumes_transient_text_without_mutating_caller_queue(tmp_path, monkeypatch):
    monkeypatch.setattr("videotrans.tts._base.config.TEMP_DIR", str(tmp_path))
    source_queue = [{
        "text": "AI giữ nguyên trong SRT",
        "tts_text": "ây ai giữ nguyên trong SRT",
        "filename": str(tmp_path / "segment.wav"),
        "volume": "+0%",
    }]

    tts = BaseTTS(queue_tts=source_queue, uuid="pronunciation-copy")

    assert source_queue[0]["text"] == "AI giữ nguyên trong SRT"
    assert tts.queue_tts[0]["text"] == "ây ai giữ nguyên trong SRT"
    assert tts.queue_tts[0]["tts_text"] == "ây ai giữ nguyên trong SRT"


def test_benchmark_fixture_contract_covers_required_cases():
    joined = "\n".join(BENCHMARK_FIXTURES)
    for expected in (
        "AI", "API", "ChatGPT", "GitHub", "Docker", "Python", "OpenRouter",
        "Gemini", "NVIDIA", "https://", "@", "3.12.14",
    ):
        assert expected in joined


def test_glossary_change_changes_cache_input_without_changing_subtitle_text():
    original = "AI remains visible"

    first_tts_text = prepare_tts_text(
        original,
        language="vi",
        glossary={"AI": "ai-first"},
    )
    second_tts_text = prepare_tts_text(
        original,
        language="vi",
        glossary={"AI": "ai-second"},
    )
    first_key = get_md5(f"vi-{first_tts_text}-voice-+0%-+0%-+0Hz-22")
    second_key = get_md5(f"vi-{second_tts_text}-voice-+0%-+0%-+0Hz-22")

    assert original == "AI remains visible"
    assert first_tts_text != second_tts_text
    assert first_key != second_key


def test_openai_compatible_adapter_receives_prepared_tts_text_on_loopback(tmp_path, monkeypatch):
    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def iter_bytes(self):
            yield b"fake-wav"

    class FakeStreamingCreate:
        def create(self, **kwargs):
            captured["request"] = kwargs
            return FakeResponse()

    class FakeOpenAI:
        def __init__(self, *, api_key, base_url):
            captured["base_url"] = base_url
            captured["api_key_seen"] = bool(api_key)
            self.audio = SimpleNamespace(
                speech=SimpleNamespace(
                    with_streaming_response=FakeStreamingCreate(),
                )
            )

    monkeypatch.setattr(_openaitts, "OpenAI", FakeOpenAI)
    monkeypatch.setattr(_openaitts, "vail_file", lambda _: False)
    monkeypatch.setattr(OPENAITTS, "convert_to_wav", lambda self, src, dst: None)
    monkeypatch.setitem(_openaitts.params, "openaitts_api", "http://127.0.0.1:8080/v1")
    monkeypatch.setitem(_openaitts.params, "openaitts_key", "test-placeholder")
    monkeypatch.setitem(_openaitts.params, "openaitts_model", "vie-neu-pilot")
    monkeypatch.setitem(_openaitts.params, "openaitts_instructions", "")

    queue = [{
        "text": "ChatGPT dùng AI",
        "tts_text": "Chát Gi Pi Ti dùng ây ai",
        "role": "voice",
        "filename": str(tmp_path / "segment.wav"),
        "rate": "+0%",
        "volume": "+0%",
        "pitch": "+0Hz",
    }]
    tts = OPENAITTS(queue_tts=queue, language="vi", uuid="openai-compatible-pilot")

    tts._run(tts.queue_tts[0], 0)

    assert captured["base_url"] == "http://127.0.0.1:8080/v1"
    assert captured["api_key_seen"] is True
    assert captured["request"]["input"] == "Chát Gi Pi Ti dùng ây ai"
    assert captured["request"]["model"] == "vie-neu-pilot"
    assert queue[0]["text"] == "ChatGPT dùng AI"


def test_main_dubbing_uses_tts_text_for_cache_without_rewriting_srt(tmp_path, monkeypatch):
    source_srt = tmp_path / "source.srt"
    target_srt = tmp_path / "target.srt"
    source_srt.write_text(
        "1\n00:00:00,000 --> 00:00:01,000\nSource text\n",
        encoding="utf-8",
    )
    target_srt.write_text(
        "1\n00:00:00,000 --> 00:00:01,000\nAI...\n",
        encoding="utf-8",
    )
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    dubbing_cache = tmp_path / "dubbing-cache"
    dubbing_cache.mkdir()

    captured = {}

    def fake_run_tts(**kwargs):
        captured["queue"] = kwargs["queue_tts"]

    monkeypatch.setattr(_stage_dubbing, "run_tts", fake_run_tts)
    monkeypatch.setattr(_stage_dubbing, "DUBBING_CACHE", str(dubbing_cache))
    monkeypatch.setattr(_stage_dubbing.app_cfg, "line_roles", {})
    monkeypatch.setitem(_stage_dubbing.settings, "save_segment_audio", False)

    processor = SimpleNamespace(
        should_dubbing=True,
        uuid="tts-text-main-workflow",
        queue_tts=[],
        cfg=SimpleNamespace(
            target_sub=str(target_srt),
            source_sub=str(source_srt),
            target_language_code="vi",
            target_dir=str(tmp_path),
            voice_rate="+0%",
            voice_role="vi-VN-HoaiMyNeural",
            volume="+0%",
            pitch="+0Hz",
            tts_type=0,
            cache_folder=str(cache_dir),
            detect_language="en",
            is_cuda=False,
            fix_punc=0,
            noextname="fixture",
        ),
        signal=lambda **kwargs: None,
        _create_ref_from_vocal=lambda: None,
    )
    processor._save_srt_target = BaseTask._save_srt_target.__get__(processor)

    DubbingMixin._tts(processor)

    item = captured["queue"][0]
    assert item["text"] == "AI..."
    assert item["tts_text"] == "ây ai..."
    expected_key = get_md5(
        "vi-ây ai...-vi-VN-HoaiMyNeural-+0%-+0%-+0Hz-0"
    )
    assert Path(item["filename"]).name.endswith(f"-{expected_key}.wav")
    assert "AI..." in target_srt.read_text(encoding="utf-8")
    assert "ây ai" not in target_srt.read_text(encoding="utf-8")
