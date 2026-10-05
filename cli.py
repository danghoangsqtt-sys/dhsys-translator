"""
pyVideoTrans CLI — command-line interface for video translation, dubbing, and transcription.

Usage examples:
  # Speech to text
  uv run cli.py --task stt --name "D:/videos/demo.mp4" --recogn_type 0 --model_name large-v3

  # Subtitle translation
  uv run cli.py --task sts --name "D:/subs/source.srt" --target_language_code en

  # Text to speech
  uv run cli.py --task tts --name "C:/subs/movie.srt" --tts_type 0 --voice_role "zh-CN-YunyangNeural"

  # Full video translation
  uv run cli.py --task vtv --name "E:/movies/clip.mp4" --source_language_code zh-cn --target_language_code en --voice_role "en-US-GuyNeural" --cuda
"""

import asyncio
import multiprocessing
import sys
import re
import uuid
import argparse
from dataclasses import asdict
from multiprocessing import freeze_support
from pathlib import Path
from typing import Dict, List, Optional

import torch.cuda

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# ---------------------------------------------------------------------------
# TEXT_DB — Vietnamese/English strings for all CLI output
# ---------------------------------------------------------------------------
_LEGACY_TEXT_DB: Dict[str, Dict[str, str]] = {
    # --- Log messages ---
    "exec_stt_task": {"legacy": "[Task] Speech Transcription (STT)", "en": "[Task] Speech Transcription (STT)"},
    "exec_tts_task": {"legacy": "[Task] Text-to-Speech (TTS)", "en": "[Task] Text-to-Speech (TTS)"},
    "exec_sts_task": {"legacy": "[Task] Subtitle Translation (STS)", "en": "[Task] Subtitle Translation (STS)"},
    "exec_vtv_task": {"legacy": "[Task] Video Translation (VTV)", "en": "[Task] Video Translation (VTV)"},
    "process_file":  {"legacy": "[File] {}", "en": "[File] {}"},
    "param_list":    {"legacy": "[Params] {}", "en": "[Params] {}"},
    "output_dir":    {"legacy": "[Output Dir] {}", "en": "[Output Dir] {}"},
    "done":          {"legacy": "[Done] Task completed successfully", "en": "[Done] Task completed successfully"},
    "failed":        {"legacy": "[Failed] Task error: {}", "en": "[Failed] Task error: {}"},

    # --- Argparse descriptions ---
    "cli_desc": {
        "legacy": "pyVideoTrans CLI Mode\nDocs: https://pyvideotrans.com/cli",
        "en": "pyVideoTrans CLI Mode\nDocs: https://pyvideotrans.com/cli"
    },
    "cli_epilog": {
        "legacy": "Examples:\n"
              "  %(prog)s --task stt --name \"D:/demo.mp4\" --recogn_type 0 --model_name large-v3\n"
              "  %(prog)s --task tts --name \"D:/demo.srt\" --tts_type 0 --voice_role \"zh-CN-YunyangNeural\"\n"
              "  %(prog)s --task sts --name \"D:/demo.srt\" --target_language_code en\n"
              "  %(prog)s --task vtv --name \"D:/demo.mp4\" --source_language_code zh-cn --target_language_code en --voice_role \"en-US-GuyNeural\"\n"
              "  %(prog)s --list providers\n"
              "  %(prog)s --list languages",
        "en": "Examples:\n"
              "  %(prog)s --task stt --name \"D:/demo.mp4\" --recogn_type 0 --model_name large-v3\n"
              "  %(prog)s --task tts --name \"D:/demo.srt\" --tts_type 0 --voice_role \"zh-CN-YunyangNeural\"\n"
              "  %(prog)s --task sts --name \"D:/demo.srt\" --target_language_code en\n"
              "  %(prog)s --task vtv --name \"D:/demo.mp4\" --source_language_code zh-cn --target_language_code en --voice_role \"en-US-GuyNeural\"\n"
              "  %(prog)s --list providers\n"
              "  %(prog)s --list languages"
    },
    "help_task": {
        "legacy": "Task type: stt(Speech to Text), tts(Text to Speech), sts(Subtitle Trans), vtv(Video Trans)",
        "en": "Task type: stt(Speech to Text), tts(Text to Speech), sts(Subtitle Trans), vtv(Video Trans)"
    },
    "help_name": {
        "legacy": "Absolute path of the file to process (wrap in quotes if path contains spaces)",
        "en": "Absolute path of the file to process (wrap in quotes if path contains spaces)"
    },
    "help_list": {
        "legacy": "List available options: providers, languages, models",
        "en": "List available options: providers, languages, models"
    },
    "help_output_dir": {
        "legacy": "Output root (default: application output; each run gets its own subdirectory)",
        "en": "Output root (default: application output; each run gets its own subdirectory)"
    },
    "help_log_level": {
        "legacy": "Log level: DEBUG, INFO, WARNING, ERROR (default: WARNING)",
        "en": "Log level: DEBUG, INFO, WARNING, ERROR (default: WARNING)"
    },
    "help_verbose": {
        "legacy": "Show verbose output (equivalent to --log-level INFO)",
        "en": "Show verbose output (equivalent to --log-level INFO)"
    },
    "help_quiet": {
        "legacy": "Quiet mode, only output errors",
        "en": "Quiet mode, only output errors"
    },

    # --- STT params ---
    "group_stt":       {"legacy": "STT (Speech Transcription) Parameters", "en": "STT (Speech Transcription) Parameters"},
    "help_recogn_type": {"legacy": "Speech recognition provider index", "en": "Speech recognition provider index"},
    "help_detect_lang":  {"legacy": "Source language of audio/video", "en": "Source language of audio/video"},
    "help_model_name": {
        "legacy": "ASR model name\nfaster-whisper(0) & openai-whisper(1) options: {}\nOthers: check GUI",
        "en": "ASR model name\nfaster-whisper(0) & openai-whisper(1) options: {}\nOthers: check GUI"
    },
    "help_cuda":           {"legacy": "Enable CUDA acceleration", "en": "Enable CUDA acceleration"},
    "help_remove_noise":   {"legacy": "Enable noise reduction", "en": "Enable noise reduction"},
    "help_enable_diariz":  {"legacy": "Enable speaker diarization", "en": "Enable speaker diarization"},
    "help_nums_diariz":    {"legacy": "Number of speakers", "en": "Number of speakers"},
    "help_rephrase":       {"legacy": "Rephrase (0=default, 1=LLM)", "en": "Rephrase (0=default, 1=LLM)"},
    "help_fix_punc":       {"legacy": "Restore punctuation", "en": "Restore punctuation"},

    # --- TTS params ---
    "group_tts":         {"legacy": "TTS (Text-to-Speech) Parameters", "en": "TTS (Text-to-Speech) Parameters"},
    "help_tts_type":     {"legacy": "TTS provider index", "en": "TTS provider index"},
    "help_voice_role":   {"legacy": "Voice role name (required for TTS)", "en": "Voice role name (required for TTS)"},
    "help_voice_rate":   {"legacy": "Speech rate (e.g. +20%%, -10%%)", "en": "Speech rate (e.g. +20%%, -10%%)"},
    "help_volume":       {"legacy": "Volume (e.g. +50%%, -30%%)", "en": "Volume (e.g. +50%%, -30%%)"},
    "help_pitch":        {"legacy": "Pitch (e.g. +10Hz, -5Hz)", "en": "Pitch (e.g. +10Hz, -5Hz)"},
    "help_voice_autorate": {"legacy": "Auto-speed audio to match subtitles", "en": "Auto-speed audio to match subtitles"},
    "help_align_sub_audio": {"legacy": "Force subtitle adjustment to align with audio", "en": "Force subtitle adjustment to align with audio"},

    # --- Translation params ---
    "group_trans":        {"legacy": "Translation Parameters", "en": "Translation Parameters"},
    "help_translate_type": {"legacy": "Translation provider index", "en": "Translation provider index"},
    "help_source_lang":   {"legacy": "Source language (auto for STS, required for VTV)", "en": "Source language (auto for STS, required for VTV)"},
    "help_target_lang":   {"legacy": "Target language (required)", "en": "Target language (required)"},

    # --- VTV extra params ---
    "group_vtv":           {"legacy": "VTV Extra Parameters", "en": "VTV Extra Parameters"},
    "help_video_autorate": {"legacy": "Auto-slow video to match subtitles", "en": "Auto-slow video to match subtitles"},
    "help_is_separate":    {"legacy": "Separate vocals and background", "en": "Separate vocals and background"},
    "help_recogn2pass":    {"legacy": "Enable 2-pass recognition", "en": "Enable 2-pass recognition"},
    "help_subtitle_type":  {"legacy": "Subtitle type (0=None, 1=Hard, 2=Soft, 3=Hard Dual, 4=Soft Dual)", "en": "Subtitle type (0=None, 1=Hard, 2=Soft, 3=Hard Dual, 4=Soft Dual)"},
    "help_clear_cache":    {"legacy": "Clear cache after finish (default)", "en": "Clear cache after finish (default)"},
    "help_no_clear_cache": {"legacy": "Do not clear cache", "en": "Do not clear cache"},

    # --- Error messages ---
    "err_missing_task": {
        "legacy": "Missing --task parameter. Choose: stt, tts, sts, vtv\nUse --help for details",
        "en": "Missing --task parameter. Choose: stt, tts, sts, vtv\nUse --help for details"
    },
    "err_file_not_found": {
        "legacy": "File not found: {}\nCheck path, wrap space-containing paths in quotes",
        "en": "File not found: {}\nCheck path, wrap space-containing paths in quotes"
    },
    "err_tts_role_required": {
        "legacy": "--voice_role is required for TTS mode\nUse --list providers to see available options",
        "en": "--voice_role is required for TTS mode\nUse --list providers to see available options"
    },
    "err_sts_target_required": {
        "legacy": "--target_language_code is required\nUse --list languages to see available options",
        "en": "--target_language_code is required\nUse --list languages to see available options"
    },
    "err_vtv_missing": {
        "legacy": "VTV mode missing required params: {}",
        "en": "VTV mode missing required params: {}"
    },
    "miss_source_lang": {"legacy": "--source_language_code", "en": "--source_language_code"},
    "miss_target_lang": {"legacy": "--target_language_code", "en": "--target_language_code"},

    # --- List output ---
    "list_providers_header": {
        "legacy": "\n=== Available Providers ===\n\n--- Speech Recognition (STT) ---",
        "en": "\n=== Available Providers ===\n\n--- Speech Recognition (STT) ---"
    },
    "list_trans_header":     {"legacy": "\n--- Translation ---", "en": "\n--- Translation ---"},
    "list_tts_header":       {"legacy": "\n--- Text-to-Speech (TTS) ---", "en": "\n--- Text-to-Speech (TTS) ---"},
    "list_languages_header": {"legacy": "\n=== Available Language Codes ===", "en": "\n=== Available Language Codes ==="},
    "list_models_header":    {"legacy": "\n=== faster-whisper Models ===", "en": "\n=== faster-whisper Models ==="},
}


# Vietnamese CLI output.  Chinese remains a valid media language code in the
# examples above, but is no longer a CLI interface locale.
_VI_TEXT = {
    "exec_stt_task": "[Tác vụ] Chuyển giọng nói thành văn bản (STT)", "exec_tts_task": "[Tác vụ] Tổng hợp giọng nói (TTS)",
    "exec_sts_task": "[Tác vụ] Dịch phụ đề (STS)", "exec_vtv_task": "[Tác vụ] Dịch video (VTV)",
    "process_file": "[Tệp] {}", "param_list": "[Tham số] {}", "output_dir": "[Thư mục xuất] {}",
    "done": "[Hoàn tất] Tác vụ đã hoàn thành", "failed": "[Lỗi] Tác vụ gặp lỗi: {}",
    "cli_desc": "Chế độ dòng lệnh pyVideoTrans\nTài liệu: https://pyvideotrans.com/cli",
    "cli_epilog": "Ví dụ:\n  %(prog)s --task stt --name \"D:/demo.mp4\" --recogn_type 0 --model_name large-v3\n  %(prog)s --task tts --name \"D:/demo.srt\" --tts_type 0 --voice_role \"zh-CN-YunyangNeural\"\n  %(prog)s --task sts --name \"D:/demo.srt\" --target_language_code en\n  %(prog)s --task vtv --name \"D:/demo.mp4\" --source_language_code zh-cn --target_language_code en --voice_role \"en-US-GuyNeural\"\n  %(prog)s --list providers\n  %(prog)s --list languages",
    "help_task": "Loại tác vụ: stt(chuyển giọng nói thành văn bản), tts(chuyển văn bản thành giọng nói), sts(dịch phụ đề), vtv(dịch video)",
    "help_name": "Đường dẫn tuyệt đối đến tệp cần xử lý (đặt trong dấu ngoặc kép nếu có khoảng trắng)",
    "help_list": "Liệt kê lựa chọn: providers, languages, models", "help_output_dir": "Thư mục xuất gốc (mặc định: thư mục output của ứng dụng; mỗi lần chạy dùng thư mục con riêng)",
    "help_log_level": "Mức nhật ký: DEBUG, INFO, WARNING, ERROR (mặc định: WARNING)", "help_verbose": "Hiện chi tiết (tương đương --log-level INFO)", "help_quiet": "Chế độ im lặng, chỉ hiện lỗi",
    "group_stt": "Tham số STT", "help_recogn_type": "Chỉ số nhà cung cấp nhận dạng giọng nói", "help_detect_lang": "Ngôn ngữ nguồn của âm thanh/video", "help_model_name": "Tên mô hình ASR\nCác lựa chọn faster-whisper(0) và openai-whisper(1): {}\nNhà cung cấp khác: xem giao diện", "help_cuda": "Bật tăng tốc CUDA", "help_remove_noise": "Bật giảm nhiễu", "help_enable_diariz": "Bật phân biệt người nói", "help_nums_diariz": "Số người nói", "help_rephrase": "Ngắt câu lại (0=mặc định, 1=LLM)", "help_fix_punc": "Khôi phục dấu câu",
    "group_tts": "Tham số TTS", "help_tts_type": "Chỉ số nhà cung cấp TTS", "help_voice_role": "Tên giọng đọc (bắt buộc cho TTS)", "help_voice_rate": "Tốc độ nói (ví dụ +20%%, -10%%)", "help_volume": "Âm lượng (ví dụ +50%%, -30%%)", "help_pitch": "Cao độ (ví dụ +10Hz, -5Hz)", "help_voice_autorate": "Tự tăng tốc âm thanh để khớp phụ đề", "help_align_sub_audio": "Buộc điều chỉnh phụ đề để khớp âm thanh",
    "group_trans": "Tham số dịch", "help_translate_type": "Chỉ số nhà cung cấp dịch", "help_source_lang": "Ngôn ngữ nguồn (auto cho STS, bắt buộc cho VTV)", "help_target_lang": "Ngôn ngữ đích (bắt buộc)",
    "group_vtv": "Tham số bổ sung cho VTV", "help_video_autorate": "Tự làm chậm video để khớp phụ đề", "help_is_separate": "Tách giọng nói và âm nền", "help_recogn2pass": "Bật nhận dạng hai lượt", "help_subtitle_type": "Loại phụ đề (0=Không, 1=Cứng, 2=Mềm, 3=Cứng song ngữ, 4=Mềm song ngữ)", "help_clear_cache": "Dọn bộ nhớ đệm sau khi xong (mặc định)", "help_no_clear_cache": "Không dọn bộ nhớ đệm",
    "err_missing_task": "Thiếu tham số --task. Chọn: stt, tts, sts, vtv\nDùng --help để xem chi tiết", "err_file_not_found": "Không tìm thấy tệp: {}\nKiểm tra đường dẫn và đặt đường dẫn có khoảng trắng trong dấu ngoặc kép", "err_tts_role_required": "--voice_role là bắt buộc cho chế độ TTS\nDùng --list providers để xem lựa chọn", "err_sts_target_required": "--target_language_code là bắt buộc\nDùng --list languages để xem ngôn ngữ", "err_vtv_missing": "VTV thiếu tham số bắt buộc: {}",
    "list_providers_header": "\n=== Nhà cung cấp khả dụng ===\n\n--- Nhận dạng giọng nói (STT) ---", "list_trans_header": "\n--- Dịch ---", "list_tts_header": "\n--- Chuyển văn bản thành giọng nói (TTS) ---", "list_languages_header": "\n=== Mã ngôn ngữ khả dụng ===", "list_models_header": "\n=== Mô hình faster-whisper ===",
}
TEXT_DB: Dict[str, Dict[str, str]] = {
    key: {"en": value["en"], "vi": _VI_TEXT.get(key, value["en"])}
    for key, value in _LEGACY_TEXT_DB.items()
}
del _LEGACY_TEXT_DB

# ---------------------------------------------------------------------------
# tr() — translation helper
# ---------------------------------------------------------------------------
_lang: str = "en"


def _configure_stdio_encoding() -> None:
    """Keep Vietnamese CLI output writable in redirected Windows consoles."""
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except (OSError, ValueError):
                pass


def set_lang(lang: str) -> None:
    """Set the global language for CLI output."""
    global _lang
    _lang = "vi" if lang in ("vi", "vi_VN") else "en"


def tr(key: str, *args) -> str:
    """Translate a TEXT_DB key to the current language."""
    lang_dict = TEXT_DB.get(key, {})
    text = lang_dict.get(_lang, lang_dict.get("en", key))
    if args:
        return text.format(*args)
    return text


# ---------------------------------------------------------------------------
# Task execution functions
# ---------------------------------------------------------------------------
def stt_fun(params: dict) -> None:
    """Execute speech-to-text task."""
    from videotrans.configure.config import app_cfg
    from videotrans.task.speech2text import SpeechToText
    from videotrans.task.taskcfg import TaskCfgSTT

    print(f"\n{tr('exec_stt_task')}")
    print(tr('process_file', params.get('name')))
    try:
        trk = SpeechToText(cfg=TaskCfgSTT(**params), out_format='srt')
        trk.prepare()
        trk.recogn()
        trk.diariz()
        trk.task_done()
        print(tr('done'))
    except Exception as e:
        print(tr('failed', str(e)), file=sys.stderr)
        raise


def tts_fun(params: dict) -> None:
    """Execute text-to-speech task."""
    from videotrans.task.dubbing import DubbingSrt
    from videotrans.task.taskcfg import TaskCfgTTS

    print(f"\n{tr('exec_tts_task')}")
    print(tr('process_file', params.get('name')))
    try:
        trk = DubbingSrt(cfg=TaskCfgTTS(**params), out_ext='wav')
        trk.prepare()
        trk.dubbing()
        trk.align()
        trk.task_done()
        print(tr('done'))
    except Exception as e:
        print(tr('failed', str(e)), file=sys.stderr)
        raise


def sts_fun(params: dict) -> None:
    """Execute subtitle translation task."""
    from videotrans.task.translate_srt import TranslateSrt
    from videotrans.task.taskcfg import TaskCfgSTS

    print(f"\n{tr('exec_sts_task')}")
    print(tr('process_file', params.get('name')))
    try:
        trk = TranslateSrt(cfg=TaskCfgSTS(**params), out_format=0)
        trk.prepare()
        trk.trans()
        trk.task_done()
        print(tr('done'))
    except Exception as e:
        print(tr('failed', str(e)), file=sys.stderr)
        raise


def vtv_fun(params: dict) -> None:
    """Execute full video translation task."""
    from videotrans.configure.config import app_cfg
    from videotrans.task.trans_create import TransCreate
    from videotrans.task.taskcfg import TaskCfgVTT

    app_cfg.current_status = 'ing'
    print(f"\n{tr('exec_vtv_task')}")
    print(tr('process_file', params.get('name')))
    try:
        trk = TransCreate(cfg=TaskCfgVTT(**params))
        trk.prepare()
        trk.recogn()
        trk.diariz()
        trk.trans()
        trk.dubbing()
        trk.align()
        trk.recogn2pass()
        trk.assembling()
        trk.task_done()
        print(tr('done'))
    except Exception as e:
        print(tr('failed', str(e)), file=sys.stderr)
        raise


# ---------------------------------------------------------------------------
# List functions
# ---------------------------------------------------------------------------
def list_providers() -> None:
    """Print available providers for all categories."""
    from videotrans import recognition, translator, tts

    print(tr('list_providers_header'))
    for i, name in enumerate(recognition.RECOGN_NAME_LIST):
        print(f"  {i:2d} = {name}")

    print(tr('list_trans_header'))
    for i, name in enumerate(translator.TRANSLASTE_NAME_LIST):
        print(f"  {i:2d} = {name}")

    print(tr('list_tts_header'))
    for i, name in enumerate(tts.TTS_NAME_LIST):
        print(f"  {i:2d} = {name}")


def list_languages() -> None:
    """Print available language codes."""
    from videotrans import translator

    print(tr('list_languages_header'))
    for code, name in translator.LANGNAME_DICT.items():
        print(f"  {code:10s}  {name}")


def list_models() -> None:
    """Print available faster-whisper models."""
    from videotrans.configure.constants import FASTER_MODELS_DICT

    print(tr('list_models_header'))
    for name, repo in FASTER_MODELS_DICT.items():
        print(f"  {name:25s}  {repo}")


# ---------------------------------------------------------------------------
# Argument parser construction
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser."""
    parser = argparse.ArgumentParser(
        description=tr("cli_desc"),
        epilog=tr("cli_epilog"),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    from videotrans import VERSION
    parser.add_argument('--version', action='version', version=f'%(prog)s {VERSION.removeprefix("v")}')

    parser.add_argument('--task', type=str, choices=['stt', 'tts', 'sts', 'vtv'],
                        help=tr("help_task"))
    parser.add_argument('--name', type=str, help=tr("help_name"))

    parser.add_argument('--list', type=str, choices=['providers', 'languages', 'models'],
                        help=tr("help_list"))
    parser.add_argument('--output-dir', type=str, default=None,
                        help=tr("help_output_dir"))
    parser.add_argument('--log-level', type=str, default='WARNING',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                        help=tr("help_log_level"))
    parser.add_argument('--verbose', '-v', action='store_true', help=tr("help_verbose"))
    parser.add_argument('--quiet', '-q', action='store_true', help=tr("help_quiet"))

    # --- STT ---
    stt_group = parser.add_argument_group(tr("group_stt"))
    stt_group.add_argument('--recogn_type', type=int, default=0, help=tr("help_recogn_type"))
    stt_group.add_argument('--detect_language', type=str, default='auto', help=tr("help_detect_lang"))
    stt_group.add_argument('--model_name', type=str, default='tiny', help=tr("help_model_name", 'tiny, base, small, medium, large-v3'))
    stt_group.add_argument('--cuda', action='store_true', help=tr("help_cuda"))
    stt_group.add_argument('--remove_noise', action='store_true', help=tr("help_remove_noise"))
    stt_group.add_argument('--enable_diariz', action='store_true', help=tr("help_enable_diariz"))
    stt_group.add_argument('--nums_diariz', type=int, default=0, help=tr("help_nums_diariz"))
    stt_group.add_argument('--rephrase', type=int, default=0, help=tr("help_rephrase"))
    stt_group.add_argument('--fix_punc', action='store_true', help=tr("help_fix_punc"))

    # --- TTS ---
    tts_group = parser.add_argument_group(tr("group_tts"))
    tts_group.add_argument('--tts_type', type=int, default=0, help=tr("help_tts_type"))
    tts_group.add_argument('--voice_role', type=str, default=None, help=tr("help_voice_role"))
    tts_group.add_argument('--voice_rate', type=str, default='+0%', help=tr("help_voice_rate"))
    tts_group.add_argument('--volume', type=str, default='+0%', help=tr("help_volume"))
    tts_group.add_argument('--pitch', type=str, default='+0Hz', help=tr("help_pitch"))
    tts_group.add_argument('--voice_autorate', action='store_true', help=tr("help_voice_autorate"))
    tts_group.add_argument('--align_sub_audio', action='store_true', help=tr("help_align_sub_audio"))

    # --- Translation ---
    trans_group = parser.add_argument_group(tr("group_trans"))
    trans_group.add_argument('--translate_type', type=int, default=0, help=tr("help_translate_type"))
    trans_group.add_argument('--source_language_code', type=str, default=None, help=tr("help_source_lang"))
    trans_group.add_argument('--target_language_code', type=str, default=None, help=tr("help_target_lang"))

    # --- VTV extra ---
    vtv_group = parser.add_argument_group(tr("group_vtv"))
    vtv_group.add_argument('--video_autorate', action='store_true', help=tr("help_video_autorate"))
    vtv_group.add_argument('--is_separate', action='store_true', help=tr("help_is_separate"))
    vtv_group.add_argument('--recogn2pass', action='store_true', help=tr("help_recogn2pass"))
    vtv_group.add_argument('--subtitle_type', type=int, default=1, help=tr("help_subtitle_type"))
    vtv_group.add_argument('--clear_cache', action='store_true', default=True, help=tr("help_clear_cache"))
    vtv_group.add_argument('--no-clear-cache', dest='clear_cache', action='store_false', help=tr("help_no_clear_cache"))

    return parser


# ---------------------------------------------------------------------------
# Parameter validation
# ---------------------------------------------------------------------------
def validate_task_params(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    """Validate required parameters for the given task type."""
    if not args.name:
        parser.error("--name is required")

    if not Path(args.name).exists():
        parser.error(tr("err_file_not_found", args.name))

    if args.task == 'tts' and not args.voice_role:
        parser.error(tr("err_tts_role_required"))

    if args.task == 'sts' and not args.target_language_code:
        parser.error(tr("err_sts_target_required"))

    if args.task == 'vtv':
        missing = []
        if not args.source_language_code:
            missing.append(tr("miss_source_lang"))
        if not args.target_language_code:
            missing.append(tr("miss_target_lang"))
        if missing:
            parser.error(tr("err_vtv_missing", ', '.join(missing)))


# ---------------------------------------------------------------------------
# Common parameter building
# ---------------------------------------------------------------------------
def build_common_params(args: argparse.Namespace, output_dir: Optional[str] = None) -> dict:
    """Build common parameters dict from parsed args."""
    from videotrans.configure.config import ROOT_DIR, TEMP_DIR
    from videotrans.util import tools
    from videotrans.util.gpus import getset_gpu

    _file_obj = tools.format_video(Path(args.name).absolute().as_posix())
    _nospacebasename = re.sub(r'[\s. #*?!:"]', '-', _file_obj["basename"])[:160].rstrip('-') or 'media'
    source_uuid = _file_obj.uuid
    while True:
        _file_obj.uuid = f'{source_uuid}-{uuid.uuid4().hex}'
        cache_folder = Path(TEMP_DIR) / _file_obj.uuid
        try:
            cache_folder.mkdir(parents=True, exist_ok=False)
            break
        except FileExistsError:
            continue
    output_root = Path(output_dir).absolute() if output_dir else Path(ROOT_DIR) / 'output'
    run_name = f'{_nospacebasename}-{_file_obj.uuid}'
    index = 1
    while True:
        target_dir = output_root / (run_name if index == 1 else f'{run_name}-{index}')
        try:
            target_dir.mkdir(parents=True, exist_ok=False)
            break
        except FileExistsError:
            index += 1

    _cache_folder = str(cache_folder)
    _file_obj['target_dir'] = str(target_dir)

    common_params = {'name': args.name, "cache_folder": _cache_folder}
    common_params.update(asdict(_file_obj))

    return common_params


def build_stt_params(args: argparse.Namespace) -> dict:
    """Build STT-specific parameters."""
    return {
        "recogn_type": args.recogn_type,
        "detect_language": args.source_language_code or args.detect_language,
        "model_name": args.model_name,
        "is_cuda": args.cuda if args.cuda and torch.cuda.is_available() else False,
        "remove_noise": args.remove_noise,
        "enable_diariz": args.enable_diariz,
        "nums_diariz": args.nums_diariz,
        "rephrase": args.rephrase,
        "fix_punc": args.fix_punc,
    }


def build_tts_params(args: argparse.Namespace) -> dict:
    """Build TTS-specific parameters."""
    return {
        "tts_type": args.tts_type,
        "voice_role": args.voice_role,
        "voice_rate": args.voice_rate,
        "volume": args.volume,
        "pitch": args.pitch,
        "is_cuda": args.cuda if args.cuda and torch.cuda.is_available() else False,
        "voice_autorate": args.voice_autorate,
        "align_sub_audio": args.align_sub_audio,
        "target_language_code": args.target_language_code,
    }


def build_sts_params(args: argparse.Namespace) -> dict:
    """Build STS-specific parameters."""
    return {
        "translate_type": args.translate_type,
        "source_language_code": args.source_language_code or "auto",
        "target_language_code": args.target_language_code,
    }


def build_vtv_params(args: argparse.Namespace) -> dict:
    """Build VTV-specific parameters."""
    return {
        "source_language": args.source_language_code,
        "source_language_code": args.source_language_code,
        "target_language": args.target_language_code,
        "target_language_code": args.target_language_code,
        **build_stt_params(args),
        **{k: v for k, v in build_tts_params(args).items()
           if k not in ('target_language_code', 'is_cuda')},
        "is_cuda": args.cuda if args.cuda and torch.cuda.is_available() else False,
        "translate_type": args.translate_type,
        "is_separate": args.is_separate,
        "recogn2pass": args.recogn2pass,
        "subtitle_type": args.subtitle_type,
        "clear_cache": args.clear_cache,
    }


# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
def setup_logging(log_level: str, verbose: bool = False, quiet: bool = False) -> None:
    """Configure logging level for the application."""
    import logging

    if quiet:
        level = logging.ERROR
    elif verbose:
        level = logging.INFO
    else:
        level = getattr(logging, log_level.upper(), logging.WARNING)

    logging.basicConfig(
        level=level,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%H:%M:%S',
        force=True,
    )


# ---------------------------------------------------------------------------
# Main entry
# ---------------------------------------------------------------------------
def main() -> int:
    """Main CLI entry point. Returns exit code (0=success, 1=error)."""
    _configure_stdio_encoding()
    # Parse language from system before anything else
    from videotrans.configure import config
    config.init_run()
    from videotrans.configure.config import defaulelang, app_cfg

    # Set language for CLI output
    set_lang(defaulelang)

    # Build parser and parse args
    parser = build_parser()
    args = parser.parse_args()

    # Handle --list before other validation
    if args.list:
        if args.list == 'providers':
            list_providers()
        elif args.list == 'languages':
            list_languages()
        elif args.list == 'models':
            list_models()
        return 0

    # Require --task when not using --list
    if not args.task:
        parser.error(tr("err_missing_task"))

    # Setup logging
    setup_logging(args.log_level, verbose=args.verbose, quiet=args.quiet)

    # Validate parameters
    validate_task_params(args, parser)

    # Set runtime flags
    app_cfg.exit_soft = False
    app_cfg.exec_mode = 'cli'

    # Get GPU info
    from videotrans.util.gpus import getset_gpu
    getset_gpu()

    # Build common params
    common_params = build_common_params(args, output_dir=args.output_dir)

    # Dispatch to task function
    task_map = {
        'stt': lambda: stt_fun({**common_params, **build_stt_params(args)}),
        'tts': lambda: tts_fun({**common_params, **build_tts_params(args)}),
        'sts': lambda: sts_fun({**common_params, **build_sts_params(args)}),
        'vtv': lambda: vtv_fun({**common_params, **build_vtv_params(args)}),
    }

    try:
        task_map[args.task]()
        print(tr('output_dir', common_params.get('target_dir', '')))
        return 0
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 1
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        return 130
    except Exception as e:
        print(tr('failed', str(e)), file=sys.stderr)
        return 1


if __name__ == "__main__":
    freeze_support()
    try:
        multiprocessing.set_start_method('spawn', force=True)
    except RuntimeError:
        pass
    sys.exit(main())
