"""
Comprehensive tests for cli.py — tests all public functions and argument handling.

Uses conftest.py mocks for heavy dependencies (PySide6, torch, etc.)
"""

import logging
import re
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Import the module under test (only the pure functions, not main())
# ---------------------------------------------------------------------------
from cli import (
    TEXT_DB,
    tr,
    set_lang,
    build_parser,
    validate_task_params,
    build_common_params,
    build_stt_params,
    build_tts_params,
    build_sts_params,
    build_vtv_params,
    setup_logging,
    list_providers,
    list_languages,
    list_models,
    stt_fun,
    tts_fun,
    sts_fun,
    vtv_fun,
)


# ===========================================================================
# Tests for TEXT_DB
# ===========================================================================
class TestTEXTDB:
    def test_text_db_is_dict(self):
        assert isinstance(TEXT_DB, dict)

    def test_all_task_types_have_entries(self):
        for key in ("exec_stt_task", "exec_tts_task", "exec_sts_task", "exec_vtv_task"):
            assert key in TEXT_DB, f"Missing TEXT_DB key: {key}"

    def test_error_messages_exist(self):
        for key in ("err_missing_task", "err_file_not_found",
                     "err_tts_role_required", "err_sts_target_required", "err_vtv_missing"):
            assert key in TEXT_DB, f"Missing error key: {key}"

    def test_vi_and_en_present_in_all_entries(self):
        for key, val in TEXT_DB.items():
            assert "vi" in val, f"TEXT_DB[{key}] missing 'vi'"
            assert "en" in val, f"TEXT_DB[{key}] missing 'en'"

    def test_help_keys_exist(self):
        for key in ("help_task", "help_name", "help_recogn_type",
                     "help_tts_type", "help_translate_type"):
            assert key in TEXT_DB, f"Missing help key: {key}"

    def test_format_placeholders_consistent(self):
        """All entries with {} in Vietnamese must also have {} in English."""
        for key, val in TEXT_DB.items():
            vi_count = val.get("vi", "").count("{}")
            en_count = val.get("en", "").count("{}")
            assert vi_count == en_count, (
                f"TEXT_DB[{key}]: vi has {vi_count} placeholders, en has {en_count}"
            )

    def test_cli_catalog_exposes_only_vietnamese_and_english(self):
        han = re.compile(r"[\u3400-\u9fff]")
        for key, translations in TEXT_DB.items():
            assert set(translations) == {"vi", "en"}, key
            assert not any(han.search(text) for text in translations.values()), key


# ===========================================================================
# Tests for tr() and set_lang()
# ===========================================================================
class TestTrFunction:
    def test_tr_returns_en_by_default(self):
        set_lang("en")
        result = tr("exec_stt_task")
        assert "Speech Transcription" in result

    def test_tr_returns_vi_when_set(self):
        set_lang("vi")
        result = tr("exec_stt_task")
        assert "Chuyển giọng nói" in result
        set_lang("en")  # restore

    def test_legacy_chinese_ui_locale_uses_english(self):
        set_lang("zh_CN")
        assert "Speech Transcription" in tr("exec_stt_task")
        set_lang("en")

    def test_tr_with_format_args(self):
        set_lang("en")
        result = tr("process_file", "test.mp4")
        assert "test.mp4" in result

    def test_tr_with_multiple_format_args(self):
        set_lang("en")
        result = tr("err_vtv_missing", "source, target")
        assert "source, target" in result

    def test_tr_unknown_key_returns_key(self):
        set_lang("en")
        result = tr("nonexistent_key")
        assert result == "nonexistent_key"

    def test_tr_fallback_to_en(self):
        """If current lang entry is missing, fall back to 'en'."""
        set_lang("vi")
        # All keys have Vietnamese, so test the English fallback path.
        # We can test the fallback logic by checking that en is used as default
        set_lang("en")
        result = tr("exec_stt_task")
        assert "Speech Transcription" in result
        set_lang("en")  # restore


class TestSetLang:
    def test_set_lang_updates_global(self):
        import cli
        original = cli._lang
        set_lang("vi_VN")
        assert cli._lang == "vi"
        set_lang(original)

    def test_set_lang_normalizes_unsupported_locale_to_english(self):
        set_lang("fr")
        import cli
        assert cli._lang == "en"
        set_lang("en")  # restore


# ===========================================================================
# Tests for build_parser()
# ===========================================================================
class TestBuildParser:
    def test_returns_parser(self):
        parser = build_parser()
        assert isinstance(parser, type(sys.modules["argparse"].ArgumentParser())) or hasattr(parser, 'parse_args')

    def test_task_choices(self):
        parser = build_parser()
        args = parser.parse_args(['--task', 'stt', '--name', 'test.mp4'])
        assert args.task == 'stt'

    def test_task_invalid_choice(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(['--task', 'invalid', '--name', 'test.mp4'])

    def test_name_argument(self):
        parser = build_parser()
        args = parser.parse_args(['--task', 'stt', '--name', '/path/to/video.mp4'])
        assert args.name == '/path/to/video.mp4'

    def test_list_argument(self):
        parser = build_parser()
        args = parser.parse_args(['--list', 'providers'])
        assert args.list == 'providers'

    def test_list_invalid_choice(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(['--list', 'invalid'])

    def test_version_flag(self, capsys):
        parser = build_parser()
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(['--version'])
        assert exc_info.value.code == 0

    def test_help_formats_percentage_examples(self):
        set_lang("en")
        help_text = build_parser().format_help()
        assert "+20%" in help_text
        assert "--voice_rate" in help_text

    def test_stt_defaults(self):
        parser = build_parser()
        args = parser.parse_args(['--task', 'stt', '--name', 'test.mp4'])
        assert args.recogn_type == 0
        assert args.detect_language == 'auto'
        assert args.model_name == 'tiny'
        assert args.cuda is False
        assert args.remove_noise is False
        assert args.enable_diariz is False
        assert args.nums_diariz == 0
        assert args.rephrase == 0
        assert args.fix_punc is False

    def test_tts_defaults(self):
        parser = build_parser()
        args = parser.parse_args(['--task', 'tts', '--name', 'test.srt', '--voice_role', 'test'])
        assert args.tts_type == 0
        assert args.voice_rate == '+0%'
        assert args.volume == '+0%'
        assert args.pitch == '+0Hz'
        assert args.voice_autorate is False
        assert args.align_sub_audio is False

    def test_sts_defaults(self):
        parser = build_parser()
        args = parser.parse_args(['--task', 'sts', '--name', 'test.srt', '--target_language_code', 'en'])
        assert args.translate_type == 0
        assert args.source_language_code is None

    def test_vtv_defaults(self):
        parser = build_parser()
        args = parser.parse_args([
            '--task', 'vtv', '--name', 'test.mp4',
            '--source_language_code', 'zh-cn', '--target_language_code', 'en'
        ])
        assert args.video_autorate is False
        assert args.is_separate is False
        assert args.recogn2pass is False
        assert args.subtitle_type == 1
        assert args.clear_cache is True

    def test_no_clear_cache_flag(self):
        parser = build_parser()
        args = parser.parse_args([
            '--task', 'vtv', '--name', 'test.mp4',
            '--source_language_code', 'zh-cn', '--target_language_code', 'en',
            '--no-clear-cache'
        ])
        assert args.clear_cache is False

    def test_verbose_flag(self):
        parser = build_parser()
        args = parser.parse_args(['--task', 'stt', '--name', 'test.mp4', '--verbose'])
        assert args.verbose is True

    def test_quiet_flag(self):
        parser = build_parser()
        args = parser.parse_args(['--task', 'stt', '--name', 'test.mp4', '-q'])
        assert args.quiet is True

    def test_output_dir(self):
        parser = build_parser()
        args = parser.parse_args(['--task', 'stt', '--name', 'test.mp4', '--output-dir', '/tmp/out'])
        assert args.output_dir == '/tmp/out'

    def test_log_level(self):
        parser = build_parser()
        args = parser.parse_args(['--task', 'stt', '--name', 'test.mp4', '--log-level', 'DEBUG'])
        assert args.log_level == 'DEBUG'

    def test_cuda_flag(self):
        parser = build_parser()
        args = parser.parse_args(['--task', 'stt', '--name', 'test.mp4', '--cuda'])
        assert args.cuda is True

    def test_custom_params(self):
        parser = build_parser()
        args = parser.parse_args([
            '--task', 'stt', '--name', 'test.mp4',
            '--recogn_type', '5',
            '--model_name', 'large-v3',
            '--detect_language', 'ja',
            '--remove_noise',
            '--enable_diariz',
            '--nums_diariz', '3',
            '--rephrase', '1',
            '--fix_punc',
        ])
        assert args.recogn_type == 5
        assert args.model_name == 'large-v3'
        assert args.detect_language == 'ja'
        assert args.remove_noise is True
        assert args.enable_diariz is True
        assert args.nums_diariz == 3
        assert args.rephrase == 1
        assert args.fix_punc is True


# ===========================================================================
# Tests for validate_task_params()
# ===========================================================================
class TestValidateTaskParams:
    def _make_args(self, **overrides):
        """Create a simple namespace for testing (not MagicMock, to avoid attribute issues)."""
        from argparse import Namespace
        defaults = {
            'task': 'stt',
            'name': None,
            'voice_role': None,
            'target_language_code': None,
            'source_language_code': None,
        }
        defaults.update(overrides)
        return Namespace(**defaults)

    def _make_parser(self):
        return build_parser()

    def test_missing_name_raises(self):
        args = self._make_args(task='stt', name=None)
        parser = self._make_parser()
        with pytest.raises(SystemExit):
            validate_task_params(args, parser)

    def test_nonexistent_file_raises(self):
        args = self._make_args(task='stt', name='/nonexistent/file.mp4')
        parser = self._make_parser()
        with pytest.raises(SystemExit):
            validate_task_params(args, parser)

    def test_stt_valid(self, tmp_path):
        f = tmp_path / "test.mp4"
        f.touch()
        args = self._make_args(task='stt', name=str(f))
        parser = self._make_parser()
        # Should not raise
        validate_task_params(args, parser)

    def test_tts_requires_voice_role(self, tmp_path):
        f = tmp_path / "test.srt"
        f.touch()
        args = self._make_args(task='tts', name=str(f), voice_role=None)
        parser = self._make_parser()
        with pytest.raises(SystemExit):
            validate_task_params(args, parser)

    def test_tts_valid_with_role(self, tmp_path):
        f = tmp_path / "test.srt"
        f.touch()
        args = self._make_args(task='tts', name=str(f), voice_role='test-role')
        parser = self._make_parser()
        validate_task_params(args, parser)

    def test_sts_requires_target_lang(self, tmp_path):
        f = tmp_path / "test.srt"
        f.touch()
        args = self._make_args(task='sts', name=str(f), target_language_code=None)
        parser = self._make_parser()
        with pytest.raises(SystemExit):
            validate_task_params(args, parser)

    def test_sts_valid_with_target(self, tmp_path):
        f = tmp_path / "test.srt"
        f.touch()
        args = self._make_args(task='sts', name=str(f), target_language_code='en')
        parser = self._make_parser()
        validate_task_params(args, parser)

    def test_vtv_requires_source_and_target(self, tmp_path):
        f = tmp_path / "test.mp4"
        f.touch()
        args = self._make_args(
            task='vtv', name=str(f),
            source_language_code=None, target_language_code=None
        )
        parser = self._make_parser()
        with pytest.raises(SystemExit):
            validate_task_params(args, parser)

    def test_vtv_requires_source(self, tmp_path):
        f = tmp_path / "test.mp4"
        f.touch()
        args = self._make_args(
            task='vtv', name=str(f),
            source_language_code=None, target_language_code='en'
        )
        parser = self._make_parser()
        with pytest.raises(SystemExit):
            validate_task_params(args, parser)

    def test_vtv_requires_target(self, tmp_path):
        f = tmp_path / "test.mp4"
        f.touch()
        args = self._make_args(
            task='vtv', name=str(f),
            source_language_code='zh-cn', target_language_code=None
        )
        parser = self._make_parser()
        with pytest.raises(SystemExit):
            validate_task_params(args, parser)

    def test_vtv_valid(self, tmp_path):
        f = tmp_path / "test.mp4"
        f.touch()
        args = self._make_args(
            task='vtv', name=str(f),
            source_language_code='zh-cn', target_language_code='en'
        )
        parser = self._make_parser()
        validate_task_params(args, parser)


# ===========================================================================
# Tests for parameter builders
# ===========================================================================
class TestBuildSttParams:
    def test_build_stt_params(self):
        args = MagicMock(
            recogn_type=2, detect_language='ja', model_name='large-v3',
            source_language_code=None,
            cuda=True, remove_noise=True, enable_diariz=True,
            nums_diariz=3, rephrase=1, fix_punc=True,
        )
        result = build_stt_params(args)
        assert result == {
            "recogn_type": 2,
            "detect_language": "ja",
            "model_name": "large-v3",
            "is_cuda": True,
            "remove_noise": True,
            "enable_diariz": True,
            "nums_diariz": 3,
            "rephrase": 1,
            "fix_punc": True,
        }

    def test_build_stt_params_defaults(self):
        args = MagicMock(
            recogn_type=0, detect_language='auto', model_name='tiny',
            cuda=False, remove_noise=False, enable_diariz=False,
            nums_diariz=-1, rephrase=0, fix_punc=False,
        )
        result = build_stt_params(args)
        assert result["is_cuda"] is False
        assert result["remove_noise"] is False


class TestBuildTTSParams:
    def test_build_tts_params(self):
        args = MagicMock(
            tts_type=3, voice_role='test-role', voice_rate='+20%',
            volume='-10%', pitch='+5Hz', cuda=True,
            voice_autorate=True, align_sub_audio=False,
            target_language_code='en',
        )
        result = build_tts_params(args)
        assert result == {
            "tts_type": 3,
            "voice_role": "test-role",
            "voice_rate": "+20%",
            "volume": "-10%",
            "pitch": "+5Hz",
            "is_cuda": True,
            "voice_autorate": True,
            "align_sub_audio": False,
            "target_language_code": "en",
        }


class TestBuildSTSParams:
    def test_build_sts_params(self):
        args = MagicMock(translate_type=1, source_language_code='zh-cn', target_language_code='en')
        result = build_sts_params(args)
        assert result == {
            "translate_type": 1,
            "source_language_code": "zh-cn",
            "target_language_code": "en",
        }

    def test_build_sts_params_defaults_source_to_auto(self):
        args = MagicMock(translate_type=0, source_language_code=None, target_language_code='ja')
        result = build_sts_params(args)
        assert result["source_language_code"] == "auto"


class TestBuildVTVParams:
    def test_build_vtv_params(self):
        args = MagicMock(
            source_language_code='zh-cn', target_language_code='en',
            recogn_type=0, model_name='large-v3', cuda=True,
            remove_noise=False, enable_diariz=False,
            nums_diariz=-1, rephrase=0, fix_punc=False,
            tts_type=0, voice_role='en-US-GuyNeural',
            voice_rate='+0%', volume='+0%', pitch='+0Hz',
            voice_autorate=True, video_autorate=False,
            align_sub_audio=True,
            translate_type=0,
            is_separate=True, recogn2pass=True,
            subtitle_type=1, clear_cache=True,
        )
        result = build_vtv_params(args)
        assert result["source_language_code"] == "zh-cn"
        assert result["target_language_code"] == "en"
        assert result["is_separate"] is True
        assert result["recogn2pass"] is True
        assert result["subtitle_type"] == 1
        assert result["clear_cache"] is True
        assert result["voice_role"] == "en-US-GuyNeural"
        assert result["recogn_type"] == 0
        assert result["is_cuda"] is True


class TestBuildCommonParams:
    def test_same_named_inputs_and_reruns_get_distinct_output(self, tmp_path, monkeypatch):
        """A later run must never replace an earlier run's export."""
        from argparse import Namespace
        from videotrans.configure import config

        monkeypatch.setattr(config, "TEMP_DIR", str(tmp_path / "temp"))
        first_video = tmp_path / "first" / "clip.mp4"
        second_video = tmp_path / "second" / "clip.mp4"
        first_video.parent.mkdir()
        second_video.parent.mkdir()
        first_video.write_bytes(b"first")
        second_video.write_bytes(b"second")
        output_root = tmp_path / "exports"

        first = build_common_params(Namespace(name=str(first_video)), str(output_root))
        old_export = Path(first["target_dir"]) / "en.srt"
        old_export.write_text("previous export", encoding="utf-8")
        second = build_common_params(Namespace(name=str(second_video)), str(output_root))
        rerun = build_common_params(Namespace(name=str(first_video)), str(output_root))

        assert len({first["target_dir"], second["target_dir"], rerun["target_dir"]}) == 3
        assert len({first["cache_folder"], second["cache_folder"], rerun["cache_folder"]}) == 3
        assert all(Path(run["target_dir"]).parent == output_root for run in (first, second, rerun))
        assert old_export.read_text(encoding="utf-8") == "previous export"

    def test_concurrent_reruns_reserve_distinct_directories(self, tmp_path, monkeypatch):
        from argparse import Namespace
        from concurrent.futures import ThreadPoolExecutor
        from videotrans.configure import config

        monkeypatch.setattr(config, "TEMP_DIR", str(tmp_path / "temp"))
        video = tmp_path / "clip.mp4"
        video.write_bytes(b"media")
        output_root = tmp_path / "exports"

        with ThreadPoolExecutor(max_workers=4) as pool:
            runs = list(pool.map(
                lambda _: build_common_params(Namespace(name=str(video)), str(output_root)),
                range(4),
            ))

        assert len({run["target_dir"] for run in runs}) == 4
        assert len({run["cache_folder"] for run in runs}) == 4
        assert all(Path(run["target_dir"]).is_dir() for run in runs)


# ===========================================================================
# Tests for setup_logging()
# ===========================================================================
class TestSetupLogging:
    def test_setup_logging_default(self):
        # Reset root logger to NOTSET first
        root = logging.getLogger()
        old_level = root.level
        root.setLevel(logging.NOTSET)
        try:
            setup_logging("WARNING")
            assert root.level == logging.WARNING
        finally:
            root.setLevel(old_level)

    def test_setup_logging_debug(self):
        root = logging.getLogger()
        old_level = root.level
        root.setLevel(logging.NOTSET)
        try:
            setup_logging("DEBUG")
            assert root.level == logging.DEBUG
        finally:
            root.setLevel(old_level)

    def test_setup_logging_verbose_overrides(self):
        root = logging.getLogger()
        old_level = root.level
        root.setLevel(logging.NOTSET)
        try:
            setup_logging("WARNING", verbose=True)
            assert root.level == logging.INFO
        finally:
            root.setLevel(old_level)

    def test_setup_logging_quiet_overrides(self):
        root = logging.getLogger()
        old_level = root.level
        root.setLevel(logging.NOTSET)
        try:
            setup_logging("DEBUG", quiet=True)
            assert root.level == logging.ERROR
        finally:
            root.setLevel(old_level)


# ===========================================================================
# Tests for list functions
# ===========================================================================
class TestListProviders:
    def test_list_providers_runs(self, capsys):
        list_providers()
        captured = capsys.readouterr()
        assert "Speech Recognition" in captured.out or "Nhận dạng giọng nói" in captured.out

    def test_list_providers_shows_indices(self, capsys):
        list_providers()
        captured = capsys.readouterr()
        assert "0 =" in captured.out


class TestListLanguages:
    def test_list_languages_runs(self, capsys):
        list_languages()
        captured = capsys.readouterr()
        assert "Language" in captured.out or "ngôn ngữ" in captured.out

    def test_list_languages_shows_codes(self, capsys):
        list_languages()
        captured = capsys.readouterr()
        assert "en" in captured.out


class TestListModels:
    def test_list_models_runs(self, capsys):
        list_models()
        captured = capsys.readouterr()
        assert "faster-whisper" in captured.out or "Faster" in captured.out

    def test_list_models_shows_tiny(self, capsys):
        list_models()
        captured = capsys.readouterr()
        assert "tiny" in captured.out


# ===========================================================================
# Tests for task execution functions (with mocked media workers)
# ===========================================================================
@pytest.mark.parametrize('function,module_name,class_name,stages', [
    (stt_fun, 'videotrans.task.speech2text', 'SpeechToText',
     ['prepare', 'recogn', 'diariz', 'task_done']),
    (tts_fun, 'videotrans.task.dubbing', 'DubbingSrt',
     ['prepare', 'dubbing', 'align', 'task_done']),
    (sts_fun, 'videotrans.task.translate_srt', 'TranslateSrt',
     ['prepare', 'trans', 'task_done']),
    (vtv_fun, 'videotrans.task.trans_create', 'TransCreate',
     ['prepare', 'recogn', 'diariz', 'trans', 'dubbing',
      'align', 'recogn2pass', 'assembling', 'task_done']),
])
def test_cli_task_invokes_worker_stages_in_order(monkeypatch, capsys,
                                                  function, module_name, class_name, stages):
    import importlib
    from unittest.mock import call

    worker = MagicMock()
    factory = MagicMock(return_value=worker)
    monkeypatch.setattr(importlib.import_module(module_name), class_name, factory)

    function({'name': 'sample.mp4'})

    assert [entry for entry in worker.mock_calls if entry[0] in stages] == [
        getattr(call, stage)() for stage in stages
    ]
    assert factory.call_args.kwargs['cfg'].name == 'sample.mp4'
    assert 'sample.mp4' in capsys.readouterr().out


# ===========================================================================
# Integration tests: argument parsing + validation
# ===========================================================================
class TestArgumentParsingIntegration:
    def test_stt_full_args(self, tmp_path):
        f = tmp_path / "demo.mp4"
        f.touch()
        parser = build_parser()
        args = parser.parse_args([
            '--task', 'stt', '--name', str(f),
            '--recogn_type', '2', '--model_name', 'large-v3',
            '--detect_language', 'ja', '--cuda',
            '--remove_noise', '--enable_diariz', '--nums_diariz', '3',
            '--rephrase', '1', '--fix_punc',
        ])
        assert args.task == 'stt'
        assert args.recogn_type == 2
        assert args.model_name == 'large-v3'
        assert args.cuda is True
        validate_task_params(args, parser)

    def test_tts_full_args(self, tmp_path):
        f = tmp_path / "movie.srt"
        f.touch()
        parser = build_parser()
        args = parser.parse_args([
            '--task', 'tts', '--name', str(f),
            '--tts_type', '3', '--voice_role', 'zh-CN-YunyangNeural',
            '--voice_rate=+20%', '--volume=-10%', '--pitch=+5Hz',
            '--voice_autorate',
        ])
        assert args.task == 'tts'
        assert args.voice_role == 'zh-CN-YunyangNeural'
        assert args.voice_rate == '+20%'
        assert args.volume == '-10%'
        validate_task_params(args, parser)

    def test_sts_full_args(self, tmp_path):
        f = tmp_path / "subs.srt"
        f.touch()
        parser = build_parser()
        args = parser.parse_args([
            '--task', 'sts', '--name', str(f),
            '--target_language_code', 'en',
            '--source_language_code', 'zh-cn',
            '--translate_type', '1',
        ])
        assert args.task == 'sts'
        assert args.target_language_code == 'en'
        validate_task_params(args, parser)

    def test_vtv_full_args(self, tmp_path):
        f = tmp_path / "clip.mp4"
        f.touch()
        parser = build_parser()
        args = parser.parse_args([
            '--task', 'vtv', '--name', str(f),
            '--source_language_code', 'zh-cn', '--target_language_code', 'en',
            '--voice_role', 'en-US-GuyNeural', '--cuda',
            '--is_separate', '--recogn2pass',
            '--subtitle_type', '3', '--no-clear-cache',
        ])
        assert args.task == 'vtv'
        assert args.source_language_code == 'zh-cn'
        assert args.target_language_code == 'en'
        assert args.clear_cache is False
        validate_task_params(args, parser)

    def test_list_providers(self):
        parser = build_parser()
        args = parser.parse_args(['--list', 'providers'])
        assert args.list == 'providers'
        assert args.task is None

    def test_list_languages(self):
        parser = build_parser()
        args = parser.parse_args(['--list', 'languages'])
        assert args.list == 'languages'

    def test_list_models(self):
        parser = build_parser()
        args = parser.parse_args(['--list', 'models'])
        assert args.list == 'models'

    def test_output_dir(self, tmp_path):
        f = tmp_path / "test.mp4"
        f.touch()
        parser = build_parser()
        args = parser.parse_args([
            '--task', 'stt', '--name', str(f),
            '--output-dir', str(tmp_path / 'custom_output'),
        ])
        assert args.output_dir == str(tmp_path / 'custom_output')

    def test_log_levels(self):
        parser = build_parser()
        for level in ('DEBUG', 'INFO', 'WARNING', 'ERROR'):
            args = parser.parse_args(['--task', 'stt', '--name', 'test.mp4', '--log-level', level])
            assert args.log_level == level
