"""Rebuild a finished translated video after the user edits its subtitles.

The task cache is deleted after a successful job, so re-export only uses files
that persist: the original input video, the dubbed audio written to the output
folder (or the input's own audio when nothing was dubbed) and the edited SRT.
Subtitles are prepared by the regular subtitle stage so wrapping, bilingual
joins and ASS styling match a normal export.
"""

import shutil
import uuid
from pathlib import Path
from types import SimpleNamespace
from typing import List, Optional, Tuple

from videotrans.configure import config
from videotrans.configure.config import logger, settings
from videotrans.task._stage_assemble import _unused_video_path
from videotrans.task._stage_subtitle import SubtitleMixin
from videotrans.task.subtitle_output import HARD_SUBTITLE_TYPES, SOFT_SUBTITLE_TYPES

UNSUPPORTED_NO_SOURCE = "reexport_unsupported_no_source"
UNSUPPORTED_NO_SUBTITLE = "reexport_unsupported_no_subtitle"
UNSUPPORTED_AUTORATE = "reexport_unsupported_autorate"


def reexport_support(receipt: dict) -> Tuple[bool, str]:
    """Return (supported, reason translation key) for a result receipt."""
    if receipt.get("video_autorate"):
        return False, UNSUPPORTED_AUTORATE
    source = receipt.get("source_video")
    if not source or not Path(source).is_file():
        return False, UNSUPPORTED_NO_SOURCE
    target_sub = receipt.get("target_sub")
    if int(receipt.get("subtitle_type", 0)) <= 0 or not target_sub or not Path(target_sub).is_file():
        return False, UNSUPPORTED_NO_SUBTITLE
    return True, ""


def _dubbed_audio(receipt: dict) -> Optional[str]:
    for raw in receipt.get("audio_paths") or []:
        if raw and Path(raw).is_file():
            return raw
    return None


def prepare_subtitles(receipt: dict, cache_folder: str) -> Tuple[str, str, int]:
    """Run the regular subtitle preparation; return (file in cache, langcode, type)."""
    cfg = SimpleNamespace(
        subtitle_type=int(receipt.get("subtitle_type", 1)),
        target_sub=receipt["target_sub"],
        source_sub=receipt.get("source_sub") or "",
        source_language_code=receipt.get("source_language_code") or "",
        target_language_code=receipt.get("target_language_code") or "",
        target_language=receipt.get("target_language") or receipt.get("target_language_code") or "",
        cache_folder=cache_folder,
        target_dir=receipt.get("target_dir") or str(Path(receipt["video_path"]).parent),
        output_srt=int(receipt.get("output_srt", 2)),
    )
    stage = SimpleNamespace(cfg=cfg)
    stage._get_join_flag = lambda: SubtitleMixin._get_join_flag(stage)
    subtitle_file, langcode = SubtitleMixin._process_subtitles(stage)
    return subtitle_file, langcode, cfg.subtitle_type


def build_reexport_command(receipt: dict, subtitle_file: str, subtitle_langcode: str,
                           subtitle_type: int, output_name: str) -> List[str]:
    """FFmpeg arguments, run with the cache folder as working directory."""
    source = Path(receipt["source_video"]).resolve().as_posix()
    audio = _dubbed_audio(receipt)
    cmd = ["-y", "-i", source]
    if audio:
        cmd += ["-i", Path(audio).resolve().as_posix()]
    if subtitle_type in SOFT_SUBTITLE_TYPES:
        cmd += ["-i", subtitle_file]
        subtitle_input = 2 if audio else 1

    if subtitle_type in HARD_SUBTITLE_TYPES:
        cmd += ["-filter_complex", f"[0:v]subtitles=filename='{subtitle_file}'[v_out]", "-map", "[v_out]"]
    else:
        cmd += ["-map", "0:v:0"]
    cmd += ["-map", "1:a:0" if audio else "0:a?"]
    if subtitle_type in SOFT_SUBTITLE_TYPES:
        cmd += ["-map", f"{subtitle_input}:s:0"]

    cmd += [
        "-c:v", "libx264",
        "-crf", str(settings.get("crf", 23)),
        "-preset", str(settings.get("preset", "medium")),
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k",
    ]
    if subtitle_type in SOFT_SUBTITLE_TYPES:
        cmd += ["-c:s", "mov_text", "-metadata:s:s:0", f"language={subtitle_langcode}"]
    cmd += ["-movflags", "+faststart", output_name]
    return cmd


def run_reexport(receipt: dict) -> dict:
    """Re-export into a new file next to the previous output and return its receipt."""
    from videotrans.util.help_ffmpeg import runffmpeg

    supported, reason = reexport_support(receipt)
    if not supported:
        raise ValueError(reason)

    cache_folder = (Path(config.TEMP_DIR) / f"reexport-{uuid.uuid4().hex[:12]}").resolve()
    cache_folder.mkdir(parents=True, exist_ok=True)
    try:
        subtitle_file, langcode, subtitle_type = prepare_subtitles(receipt, cache_folder.as_posix())
        output = _unused_video_path(Path(receipt["video_path"]))
        temp_output = "reexport.mp4"
        cmd = build_reexport_command(receipt, subtitle_file, langcode, subtitle_type, temp_output)
        logger.debug(f"[reexport] {cmd=}")
        runffmpeg(cmd, cmd_dir=cache_folder.as_posix(), force_cpu=True)
        produced = cache_folder / temp_output
        if not produced.is_file() or produced.stat().st_size == 0:
            raise RuntimeError("FFmpeg did not produce the re-exported video")
        shutil.move(str(produced), str(output))
    finally:
        shutil.rmtree(cache_folder, ignore_errors=True)

    updated = dict(receipt)
    updated["video_path"] = str(output)
    updated["subtitle_type"] = subtitle_type
    return updated
