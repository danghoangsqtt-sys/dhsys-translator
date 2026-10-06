"""Exercise a Windows candidate through its bundled Python interpreter.

Run with ``sp.exe smoke_frozen.py report.json`` from outside the install tree.
The script uses generated media and never calls a remote provider.
"""

import contextlib
import io
import json
import os
from pathlib import Path
import re
import runpy
import subprocess
import sys
import tempfile
import traceback


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def run_check(cli_script):
    require(getattr(sys, "frozen", False), "smoke must run inside the packaged executable")
    bundle = Path(sys.executable).resolve().parent
    install_root = bundle / "_internal"
    ffmpeg = install_root / "ffmpeg" / "ffmpeg.exe"
    ffprobe = install_root / "ffmpeg" / "ffprobe.exe"
    require(install_root.is_dir(), "missing bundled Python resources")
    require(ffmpeg.is_file() and ffprobe.is_file(), "missing bundled FFmpeg tools")

    from videotrans.configure._paths import ROOT_DIR, resource_path

    user_data = Path(ROOT_DIR).resolve()
    require(user_data.is_dir(), "frozen user-data directory was not created")
    require(user_data != bundle and bundle not in user_data.parents,
            "frozen user data is inside the installation")
    require(resource_path("videotrans", "styles", "style.qss").is_file(),
            "bundled style.qss could not be resolved")
    require(resource_path("videotrans", "styles", "light.qss").is_file(),
            "bundled light.qss could not be resolved")

    bundled_language_dir = install_root / "videotrans" / "language"
    bundled_catalogs = {path.name for path in bundled_language_dir.glob("*.json")}
    require(bundled_catalogs == {"en_US.json", "vi_VN.json"},
            f"unexpected bundled UI catalogs: {sorted(bundled_catalogs)}")

    from videotrans.configure._i18n import UI_LOCALES
    from videotrans.configure._languages_dict import EDGE_LANGUANGES_CODE
    from videotrans.translator import LANGNAME_DICT

    require(UI_LOCALES == ("vi_VN", "en_US"),
            f"unexpected UI locale allowlist: {UI_LOCALES}")
    require({"zh-cn", "zh-tw"}.issubset(LANGNAME_DICT),
            "Chinese source/target media languages are missing")
    require({"zh-cn", "zh-tw", "yue"}.issubset(EDGE_LANGUANGES_CODE),
            "Chinese or Cantonese TTS media languages are missing")

    from faster_whisper.utils import get_assets_path
    from faster_whisper.vad import get_vad_model

    vad_asset = Path(get_assets_path()) / "silero_vad_v6.onnx"
    require(vad_asset.is_file(), "bundled faster-whisper Silero VAD model is missing")
    vad_model = get_vad_model()
    require(vad_model.session is not None, "bundled Silero VAD model did not load")

    import zhconv
    require(zhconv.convert("繁體中文", "zh-cn") == "繁体中文",
            "bundled zhconv dictionary did not load")

    from videotrans import get_class
    from videotrans import recognition
    from videotrans import translator

    recognizer = get_class(recognition.FASTER_WHISPER, "recognition", recognition.ID_NAME_DICT)
    require(recognizer.__module__ == "videotrans.recognition._whisper",
            "dynamic speech recognizer resolved to the wrong module")
    provider = get_class(translator.GOOGLE_INDEX, "translator", translator.ID_NAME_DICT)
    require(provider.__module__ == "videotrans.translator._google",
            "dynamic translator provider resolved to the wrong module")
    fallback_provider = get_class(translator.MICROSOFT_INDEX, "translator", translator.ID_NAME_DICT)
    require(fallback_provider.__module__ == "videotrans.translator._microsoft",
            "dynamic Microsoft fallback provider resolved to the wrong module")

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    from videotrans.winform import get_win

    app = QApplication.instance() or QApplication([])
    dialog = get_win("chatgpt")
    require(dialog is not None and dialog.isVisible(), "dynamic chatgpt dialog did not open")
    dialog.close()
    app.processEvents()

    from videotrans import VERSION
    require(cli_script.is_file(), "missing external CLI script")
    cli_output = io.StringIO()
    prior_argv = sys.argv
    try:
        sys.argv = [str(cli_script), "--version"]
        with contextlib.redirect_stdout(cli_output):
            try:
                runpy.run_path(str(cli_script), run_name="__main__")
            except SystemExit as cli_exit:
                require(cli_exit.code in (None, 0),
                        f"packaged CLI --version exited with {cli_exit.code}")
    finally:
        sys.argv = prior_argv
    require(VERSION.removeprefix("v") in cli_output.getvalue(),
            f"packaged CLI did not report version {VERSION}")

    cli_languages = io.StringIO()
    try:
        sys.argv = [str(cli_script), "--list", "languages"]
        with contextlib.redirect_stdout(cli_languages):
            try:
                runpy.run_path(str(cli_script), run_name="__main__")
            except SystemExit as cli_exit:
                require(cli_exit.code in (None, 0),
                        f"packaged CLI language list exited with {cli_exit.code}")
    finally:
        sys.argv = prior_argv
    language_output = cli_languages.getvalue()
    require("zh-cn" in language_output and "zh-tw" in language_output,
            "packaged CLI removed Chinese media language codes")
    require(not re.search(r"[\u3400-\u9fff]", language_output),
            "packaged CLI emitted Chinese interface text")

    from videotrans.util.help_srt import get_subtitle_from_srt

    sample_srt = "1\n00:00:00,000 --> 00:00:00,400\nCandidate smoke\n"
    parsed = get_subtitle_from_srt(sample_srt, is_file=False)
    require(len(parsed) == 1 and parsed[0]["text"] == "Candidate smoke",
            "bundled SRT parser failed")

    with tempfile.TemporaryDirectory(prefix="pyvideotrans-candidate-") as temporary:
        temporary_path = Path(temporary)
        media = temporary_path / "sample.mp4"
        subtitle = temporary_path / "fixture.srt"
        hard_media = temporary_path / "hard.mp4"
        soft_media = temporary_path / "soft.mp4"
        subtitle.write_text(
            "1\n00:00:00,250 --> 00:00:01,750\nVISIBLE SUBTITLE\n",
            encoding="utf-8",
        )
        subprocess.run([
            str(ffmpeg), "-hide_banner", "-loglevel", "error", "-y",
            "-f", "lavfi", "-i", "color=c=black:s=320x180:r=10:d=2",
            "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000:duration=2",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-shortest", str(media),
        ], check=True, capture_output=True, text=True, timeout=30)
        require(media.is_file() and media.stat().st_size > 0,
                "bundled FFmpeg did not create an MP4")
        probe = subprocess.run([
            str(ffprobe), "-v", "error", "-show_entries", "stream=codec_type",
            "-of", "json", str(media),
        ], check=True, capture_output=True, text=True, timeout=30)
        streams = {stream["codec_type"] for stream in json.loads(probe.stdout)["streams"]}
        require({"video", "audio"}.issubset(streams),
                "generated MP4 lacks an audio or video stream")

        subprocess.run([
            str(ffmpeg), "-hide_banner", "-loglevel", "error", "-y",
            "-i", "sample.mp4", "-vf", "subtitles=fixture.srt",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "copy", "hard.mp4",
        ], cwd=temporary, check=True, capture_output=True, text=True, timeout=30)

        def decoded_gray_frame(filename):
            result = subprocess.run([
                str(ffmpeg), "-hide_banner", "-loglevel", "error",
                "-ss", "1", "-i", filename, "-frames:v", "1",
                "-f", "rawvideo", "-pix_fmt", "gray", "pipe:1",
            ], cwd=temporary, check=True, capture_output=True, timeout=30)
            return result.stdout

        baseline_frame = decoded_gray_frame("sample.mp4")
        hard_frame = decoded_gray_frame("hard.mp4")
        require(len(hard_frame) == len(baseline_frame) == 320 * 180,
                "hard-subtitle decoded frame has an unexpected size")
        hard_frame_delta = sum(hard_frame) - sum(baseline_frame)
        require(hard_frame != baseline_frame and hard_frame_delta > 10_000,
                "hard subtitle is not visible in the decoded frame")

        subprocess.run([
            str(ffmpeg), "-hide_banner", "-loglevel", "error", "-y",
            "-i", "sample.mp4", "-i", "fixture.srt",
            "-map", "0:v", "-map", "0:a?", "-map", "1:0",
            "-c:v", "copy", "-c:a", "copy", "-c:s", "mov_text",
            "-metadata:s:s:0", "language=vie", "soft.mp4",
        ], cwd=temporary, check=True, capture_output=True, text=True, timeout=30)
        soft_probe = subprocess.run([
            str(ffprobe), "-v", "error", "-select_streams", "s",
            "-show_entries", "stream=index,codec_name,codec_type:stream_tags=language",
            "-of", "json", "soft.mp4",
        ], cwd=temporary, check=True, capture_output=True, text=True, timeout=30)
        soft_streams = json.loads(soft_probe.stdout)["streams"]
        require(len(soft_streams) == 1,
                f"soft subtitle expected one stream, found {len(soft_streams)}")
        soft_stream = soft_streams[0]
        require(soft_stream.get("codec_type") == "subtitle",
                "soft subtitle stream has the wrong media type")
        require(soft_stream.get("codec_name") == "mov_text",
                "soft subtitle stream is not mov_text")
        require(soft_stream.get("tags", {}).get("language") == "vie",
                "soft subtitle stream language metadata is not vie")

    return {
        "bundle": str(bundle),
        "user_data": str(user_data),
        "provider": provider.__module__,
        "fallback_provider": fallback_provider.__module__,
        "recognizer": recognizer.__module__,
        "dialog": "videotrans.winform.chatgpt",
        "cli_version": cli_output.getvalue().strip(),
        "ui_catalogs": sorted(bundled_catalogs),
        "ui_locales": list(UI_LOCALES),
        "chinese_media_codes": ["zh-cn", "zh-tw", "yue"],
        "srt_items": len(parsed),
        "media_streams": sorted(streams),
        "hard_subtitle_frame_delta": hard_frame_delta,
        "soft_subtitle_stream": soft_stream,
        "silero_vad": str(vad_asset),
        "zhconv": "繁體中文 -> 繁体中文",
    }


def main():
    if len(sys.argv) < 3:
        return 2
    report = Path(sys.argv[1]).resolve()
    cli_script = Path(sys.argv[2]).resolve()
    try:
        result = {"status": "pass", "checks": run_check(cli_script)}
        exit_code = 0
    except BaseException as error:
        result = {"status": "fail", "error": str(error), "traceback": traceback.format_exc()}
        exit_code = 1
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
