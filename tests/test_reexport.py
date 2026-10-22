import os
import shutil
import subprocess
from pathlib import Path

import pytest

from videotrans.task import reexport
from videotrans.task.reexport import (
    UNSUPPORTED_AUTORATE,
    UNSUPPORTED_NO_SOURCE,
    UNSUPPORTED_NO_SUBTITLE,
    build_reexport_command,
    reexport_support,
)

ROOT = Path(__file__).resolve().parents[1]


def _files(tmp_path, *, audio=True):
    out = tmp_path / "out"
    out.mkdir()
    source = tmp_path / "src.mp4"
    source.write_bytes(b"0")
    target = out / "vi.srt"
    target.write_text("1\n00:00:00,500 --> 00:00:01,500\nXin chào\n", encoding="utf-8")
    receipt = {
        "subtitle_type": 1,
        "video_path": str(out / "clip-vi.mp4"),
        "source_video": str(source),
        "target_sub": str(target),
        "source_sub": "",
        "target_dir": str(out),
        "audio_paths": [],
        "video_autorate": False,
    }
    if audio:
        dubbed = out / "vi.m4a"
        dubbed.write_bytes(b"0")
        receipt["audio_paths"] = [str(dubbed)]
    return receipt


def test_support_reasons(tmp_path):
    receipt = _files(tmp_path)
    assert reexport_support(receipt) == (True, "")
    assert reexport_support(dict(receipt, video_autorate=True)) == (False, UNSUPPORTED_AUTORATE)
    assert reexport_support(dict(receipt, source_video=str(tmp_path / "none.mp4"))) == (False, UNSUPPORTED_NO_SOURCE)
    assert reexport_support(dict(receipt, subtitle_type=0)) == (False, UNSUPPORTED_NO_SUBTITLE)
    assert reexport_support(dict(receipt, target_sub="")) == (False, UNSUPPORTED_NO_SUBTITLE)
    legacy = {k: v for k, v in receipt.items() if k not in ("source_video", "target_sub")}
    assert reexport_support(legacy)[0] is False


def test_hard_subtitle_command_burns_ass_and_uses_dubbed_audio(tmp_path):
    receipt = _files(tmp_path)
    cmd = build_reexport_command(receipt, "end.ass", "vie", 1, "reexport.mp4")

    assert cmd[cmd.index("-filter_complex") + 1] == "[0:v]subtitles=filename='end.ass'[v_out]"
    assert ["-map", "[v_out]"] == cmd[cmd.index("[v_out]") - 1:cmd.index("[v_out]") + 1]
    assert "1:a:0" in cmd
    assert "-c:s" not in cmd
    assert cmd[-1] == "reexport.mp4"
    assert Path(cmd[cmd.index("-i") + 1]).is_absolute()


def test_soft_subtitle_command_without_dubbing_maps_original_audio(tmp_path):
    receipt = _files(tmp_path, audio=False)
    cmd = build_reexport_command(receipt, "end.srt", "vie", 2, "reexport.mp4")

    assert cmd.count("-i") == 2
    assert "0:a?" in cmd
    assert "1:s:0" in cmd
    assert cmd[cmd.index("-c:s") + 1] == "mov_text"
    assert "language=vie" in cmd
    assert "-filter_complex" not in cmd


def test_bilingual_soft_command_with_dubbing_maps_third_input(tmp_path):
    receipt = _files(tmp_path)
    cmd = build_reexport_command(receipt, "shuang.srt", "vie", 4, "reexport.mp4")

    assert cmd.count("-i") == 3
    assert "1:a:0" in cmd
    assert "2:s:0" in cmd


def test_run_reexport_rejects_unsupported_receipt(tmp_path):
    with pytest.raises(ValueError, match=UNSUPPORTED_AUTORATE):
        reexport.run_reexport(dict(_files(tmp_path), video_autorate=True))


FFMPEG_DIR = ROOT / "ffmpeg"


@pytest.mark.skipif(not (FFMPEG_DIR / "ffmpeg.exe").exists() and shutil.which("ffmpeg") is None,
                    reason="FFmpeg is not available")
def test_real_reexport_writes_new_files_without_replacing_previous(tmp_path, monkeypatch):
    from videotrans.configure import config

    if (FFMPEG_DIR / "ffmpeg.exe").exists():
        monkeypatch.setenv("PATH", str(FFMPEG_DIR) + os.pathsep + os.environ.get("PATH", ""))
    monkeypatch.setattr(config, "TEMP_DIR", str(tmp_path / "managed-temp"))
    monkeypatch.setattr(reexport, "settings", {"crf": 35, "preset": "ultrafast"})

    out = tmp_path / "out"
    out.mkdir()
    source = tmp_path / "src.mp4"
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc=size=160x90:rate=10",
         "-f", "lavfi", "-i", "sine=frequency=440", "-t", "2", "-c:v", "libx264",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(source)],
        check=True,
    )
    shutil.copy(source, out / "clip-vi.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "sine=frequency=660",
                    "-t", "2", "-c:a", "aac", str(out / "vi.m4a")], check=True)
    (out / "vi.srt").write_text("1\n00:00:00,200 --> 00:00:01,800\nXin chào đã sửa\n", encoding="utf-8")
    receipt = {
        "subtitle_type": 2,
        "video_path": str(out / "clip-vi.mp4"),
        "source_video": str(source),
        "target_sub": str(out / "vi.srt"),
        "source_sub": "",
        "target_dir": str(out),
        "audio_paths": [str(out / "vi.m4a")],
        "source_language_code": "en",
        "target_language_code": "vi",
        "target_language": "vi",
        "output_srt": 2,
        "video_autorate": False,
    }
    previous = (out / "clip-vi.mp4").read_bytes()

    soft = reexport.run_reexport(receipt)
    hard = reexport.run_reexport(dict(receipt, subtitle_type=1))

    assert Path(soft["video_path"]).name == "clip-vi-2.mp4"
    assert Path(hard["video_path"]).name == "clip-vi-3.mp4"
    assert (out / "clip-vi.mp4").read_bytes() == previous
    streams = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,codec_name", "-of", "csv=p=0", soft["video_path"]],
        capture_output=True, text=True, check=True,
    ).stdout
    assert "mov_text,subtitle" in streams
    assert not any(Path(config.TEMP_DIR).glob("reexport-*"))
