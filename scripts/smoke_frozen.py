"""Exercise a Windows candidate through its bundled Python interpreter.

Run with ``sp.exe smoke_frozen.py report.json`` from outside the install tree.
The script uses generated media and never calls a remote provider.
"""

import contextlib
import io
import json
import os
from pathlib import Path
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
    ffmpeg = bundle / "ffmpeg" / "ffmpeg.exe"
    ffprobe = bundle / "ffmpeg" / "ffprobe.exe"
    require(install_root.is_dir(), "missing bundled Python resources")
    require(ffmpeg.is_file() and ffprobe.is_file(), "missing bundled FFmpeg tools")

    from videotrans.configure._paths import ROOT_DIR, resource_path

    user_data = Path(ROOT_DIR).resolve()
    require(user_data.is_dir(), "frozen user-data directory was not created")
    require(user_data != bundle and bundle not in user_data.parents,
            "frozen user data is inside the installation")
    require(resource_path("videotrans", "styles", "style.qss").is_file(),
            "bundled style.qss could not be resolved")

    from videotrans import get_class
    from videotrans import recognition
    from videotrans import translator

    recognizer = get_class(recognition.FASTER_WHISPER, "recognition", recognition.ID_NAME_DICT)
    require(recognizer.__module__ == "videotrans.recognition._whisper",
            "dynamic speech recognizer resolved to the wrong module")
    provider = get_class(translator.GOOGLE_INDEX, "translator", translator.ID_NAME_DICT)
    require(provider.__module__ == "videotrans.translator._google",
            "dynamic translator provider resolved to the wrong module")

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

    from videotrans.util.help_srt import get_subtitle_from_srt

    sample_srt = "1\n00:00:00,000 --> 00:00:00,400\nCandidate smoke\n"
    parsed = get_subtitle_from_srt(sample_srt, is_file=False)
    require(len(parsed) == 1 and parsed[0]["text"] == "Candidate smoke",
            "bundled SRT parser failed")

    with tempfile.TemporaryDirectory(prefix="pyvideotrans-candidate-") as temporary:
        media = Path(temporary) / "sample.mp4"
        subprocess.run([
            str(ffmpeg), "-hide_banner", "-loglevel", "error", "-y",
            "-f", "lavfi", "-i", "color=c=black:s=64x64:r=10",
            "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=16000",
            "-t", "0.4", "-c:v", "mpeg4", "-c:a", "aac", "-shortest", str(media),
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

    return {
        "bundle": str(bundle),
        "user_data": str(user_data),
        "provider": provider.__module__,
        "recognizer": recognizer.__module__,
        "dialog": "videotrans.winform.chatgpt",
        "cli_version": cli_output.getvalue().strip(),
        "srt_items": len(parsed),
        "media_streams": sorted(streams),
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
