import wave
from types import SimpleNamespace

from scripts import benchmark_tts_pronunciation as benchmark


def _write_silent_wav(path, seconds=1.0, sample_rate=8000):
    frame_count = int(seconds * sample_rate)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(b"\x00\x00" * frame_count)


def test_benchmark_report_uses_basename_and_includes_required_metric_fields(tmp_path):
    audio = tmp_path / "01-ai.wav"
    _write_silent_wav(audio, seconds=1.0)
    queue = [{
        "filename": str(audio),
        "target_seconds": 1.5,
    }]

    result = benchmark._result_from_queue("edge", queue)

    assert result["audio"][0]["audio_file"] == "01-ai.wav"
    assert str(tmp_path) not in str(result)
    assert result["pronunciation_accuracy"] == "pending_human_review"
    assert result["naturalness"] == "pending_human_review"
    assert result["voice_continuity"] == "pending_human_review"
    assert "duration_alignment" in result
    assert "universal quality" in result["quality_claim"]


def test_failed_provider_report_does_not_store_exception_message():
    result = benchmark._failed(
        "vieneu",
        RuntimeError(r"secret-token C:\\Users\\private\\reference.wav"),
    )

    rendered = str(result)
    assert result["reason"] == "provider_execution_failed"
    assert result["error_type"] == "RuntimeError"
    assert "secret-token" not in rendered
    assert "reference.wav" not in rendered


def test_vieneu_failure_restores_openai_settings_and_keeps_report_sanitized(tmp_path, monkeypatch):
    original = {
        "openaitts_api": benchmark.params.get("openaitts_api"),
        "openaitts_key": benchmark.params.get("openaitts_key"),
        "openaitts_model": benchmark.params.get("openaitts_model"),
        "openaitts_instructions": benchmark.params.get("openaitts_instructions"),
    }
    monkeypatch.setattr(
        benchmark,
        "run_tts",
        lambda **kwargs: (_ for _ in ()).throw(RuntimeError(r"key=private C:\\secret\\voice.wav")),
    )
    args = SimpleNamespace(
        edge_voice="vi-VN-HoaiMyNeural",
        vieneu_url="http://127.0.0.1:8000/v1",
        vieneu_model="vie-neu-pilot",
        vieneu_voice="default",
        vieneu_key_env="PYVIDEOTRANS_TEST_MISSING_KEY",
        cuda=False,
    )

    result = benchmark._run_provider("vieneu", tmp_path / "vieneu", args)

    assert result["status"] == "failed"
    assert "private" not in str(result)
    assert "voice.wav" not in str(result)
    for key, value in original.items():
        assert benchmark.params.get(key) == value


def test_vieneu_benchmark_rejects_non_loopback_endpoint():
    assert benchmark._is_loopback_url("http://127.0.0.1:8000/v1") is True
    assert benchmark._is_loopback_url("http://localhost:8000/v1") is True
    assert benchmark._is_loopback_url("https://example.com/v1") is False


def test_benchmark_exit_code_requires_every_requested_provider_to_pass():
    assert benchmark._exit_code([{"status": "pass"}]) == 0
    assert benchmark._exit_code([{"status": "pass"}, {"status": "skipped"}]) == 2
    assert benchmark._exit_code([{"status": "failed"}]) == 2
    assert benchmark._exit_code([]) == 2
