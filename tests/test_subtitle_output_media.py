import json
import shutil
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from videotrans.task import _stage_assemble, _stage_subtitle
from videotrans.task._stage_assemble import AssembleMixin
from videotrans.task._stage_subtitle import SubtitleMixin


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
        "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000:duration=2",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-shortest", video,
    )
    return video, subtitle


class _PipelineFixture(AssembleMixin, SubtitleMixin):
    def __init__(self, cfg, video_info):
        self.cfg = cfg
        self.video_info = video_info
        self.should_hebing = True
        self.should_dubbing = False
        self.is_copy_video = True
        self.video_codec_num = 264
        self.precent = 1
        self.hasend = False
        self.uuid = "subtitle-media-fixture"

    @staticmethod
    def _exit():
        return False

    @staticmethod
    def signal(**kwargs):
        return None


def _render_with_product_pipeline(
    tmp_path: Path, monkeypatch, subtitle_type: int
) -> tuple[Path, Path]:
    source_video, target_subtitle = _fixture(tmp_path)
    source_subtitle = tmp_path / "source.srt"
    source_subtitle.write_text(
        "1\n00:00:00,250 --> 00:00:01,750\nSOURCE SUBTITLE\n",
        encoding="utf-8",
    )
    cache = tmp_path / "cache"
    output = tmp_path / "output"
    cache.mkdir()
    output.mkdir()
    novoice = cache / "novoice.mp4"
    shutil.copy2(source_video, novoice)
    result = output / ("hard.mp4" if subtitle_type == 1 else "soft.mp4")
    cfg = SimpleNamespace(
        name=str(source_video),
        novoice_mp4=str(novoice),
        target_sub=str(target_subtitle),
        source_sub=str(source_subtitle),
        target_dir=str(output),
        cache_folder=str(cache),
        target_wav_output=str(output / "vi.m4a"),
        targetdir_mp4=str(result),
        source_language_code="en",
        target_language_code="vi",
        target_language="Vietnamese",
        subtitle_type=subtitle_type,
        output_srt=2,
        video_autorate=False,
    )
    pipeline = _PipelineFixture(
        cfg,
        {"time": 2000, "streams_audio": 1, "video_fps": 10},
    )
    fixture_settings = {
        "out_video_ext": ".mp4",
        "video_codec": 264,
        "crf": 23,
        "preset": "medium",
        "fps_mode": "vfr",
        "force_lib": True,
        "cjk_len": 15,
        "other_len": 60,
    }
    monkeypatch.setattr(_stage_assemble, "settings", fixture_settings)
    monkeypatch.setattr(_stage_subtitle, "settings", fixture_settings)
    monkeypatch.setattr(_stage_assemble.app_cfg, "video_codec", "libx264")
    monkeypatch.setattr(
        _stage_subtitle.translator,
        "get_subtitle_code",
        lambda **kwargs: "vie",
    )

    pipeline._join_video_audio_srt()

    assert result.is_file()
    return source_video, result


def _decoded_gray_frame(video: Path) -> bytes:
    result = _run(
        FFMPEG, "-hide_banner", "-loglevel", "error",
        "-ss", "1", "-i", video, "-frames:v", "1",
        "-f", "rawvideo", "-pix_fmt", "gray", "pipe:1",
        capture_output=True,
    )
    return result.stdout


def test_hard_subtitle_is_visible_in_decoded_frame(tmp_path, monkeypatch):
    video, hard = _render_with_product_pipeline(tmp_path, monkeypatch, 1)

    baseline_frame = _decoded_gray_frame(video)
    hard_frame = _decoded_gray_frame(hard)

    assert len(hard_frame) == len(baseline_frame) == 320 * 180
    assert hard_frame != baseline_frame
    assert sum(hard_frame) > sum(baseline_frame) + 10_000


def test_soft_subtitle_has_one_language_tagged_stream(tmp_path, monkeypatch):
    _, soft = _render_with_product_pipeline(tmp_path, monkeypatch, 2)

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
