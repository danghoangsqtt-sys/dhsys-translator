import json
import shutil
import subprocess
from pathlib import Path

import pytest


FFMPEG = shutil.which("ffmpeg")
FFPROBE = shutil.which("ffprobe")
pytestmark = pytest.mark.skipif(
    not FFMPEG or not FFPROBE,
    reason="FFmpeg and ffprobe are required for subtitle media evidence",
)


def _run(*args: str, capture_output: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(
        [str(arg) for arg in args],
        check=True,
        capture_output=capture_output,
    )


def _fixture(tmp_path: Path) -> tuple[Path, Path]:
    video = tmp_path / "base.mp4"
    subtitle = tmp_path / "fixture.srt"
    subtitle.write_text(
        "1\n00:00:00,250 --> 00:00:01,750\nVISIBLE SUBTITLE\n",
        encoding="utf-8",
    )
    _run(
        FFMPEG, "-hide_banner", "-loglevel", "error", "-y",
        "-f", "lavfi", "-i", "color=c=black:s=320x180:r=10:d=2",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", video,
    )
    return video, subtitle


def _decoded_gray_frame(video: Path) -> bytes:
    result = _run(
        FFMPEG, "-hide_banner", "-loglevel", "error",
        "-ss", "1", "-i", video, "-frames:v", "1",
        "-f", "rawvideo", "-pix_fmt", "gray", "pipe:1",
        capture_output=True,
    )
    return result.stdout


def test_hard_subtitle_is_visible_in_decoded_frame(tmp_path):
    video, subtitle = _fixture(tmp_path)
    hard = tmp_path / "hard.mp4"
    escaped = subtitle.as_posix().replace(":", "\\:")
    _run(
        FFMPEG, "-hide_banner", "-loglevel", "error", "-y",
        "-i", video, "-vf", f"subtitles=filename='{escaped}'",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-an", hard,
    )

    baseline_frame = _decoded_gray_frame(video)
    hard_frame = _decoded_gray_frame(hard)

    assert len(hard_frame) == len(baseline_frame) == 320 * 180
    assert hard_frame != baseline_frame
    assert sum(hard_frame) > sum(baseline_frame) + 10_000


def test_soft_subtitle_has_one_language_tagged_stream(tmp_path):
    video, subtitle = _fixture(tmp_path)
    soft = tmp_path / "soft.mp4"
    _run(
        FFMPEG, "-hide_banner", "-loglevel", "error", "-y",
        "-i", video, "-i", subtitle,
        "-map", "0:v", "-map", "1:s",
        "-c:v", "copy", "-c:s", "mov_text",
        "-metadata:s:s:0", "language=vie", soft,
    )

    result = _run(
        FFPROBE, "-v", "error", "-select_streams", "s",
        "-show_entries", "stream=index,codec_name,codec_type:stream_tags=language",
        "-of", "json", soft, capture_output=True,
    )
    streams = json.loads(result.stdout)["streams"]

    assert len(streams) == 1
    assert streams[0]["codec_type"] == "subtitle"
    assert streams[0]["codec_name"] == "mov_text"
    assert streams[0]["tags"]["language"] == "vie"
