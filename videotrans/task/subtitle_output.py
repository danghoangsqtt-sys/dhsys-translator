"""Stable subtitle-output mapping and completion receipt data."""

from pathlib import Path


# The tuple position is the persisted ``subtitle_type`` value. Never reorder it.
SUBTITLE_TYPE_KEYS = (
    "nosubtitle",
    "embedsubtitle",
    "softsubtitle",
    "embedsubtitle2",
    "softsubtitle2",
)
HARD_SUBTITLE_TYPES = frozenset({1, 3})
SOFT_SUBTITLE_TYPES = frozenset({2, 4})
BILINGUAL_SUBTITLE_TYPES = frozenset({3, 4})


def subtitle_type_key(subtitle_type: int) -> str:
    try:
        index = int(subtitle_type)
        if index < 0 or index >= len(SUBTITLE_TYPE_KEYS):
            raise IndexError(index)
        return SUBTITLE_TYPE_KEYS[index]
    except (IndexError, TypeError, ValueError):
        return SUBTITLE_TYPE_KEYS[1]


def build_output_receipt(cfg) -> dict:
    """Build serializable output facts after a translated-video task succeeds."""
    subtitle_type = int(getattr(cfg, "subtitle_type", 1))
    video_path = str(getattr(cfg, "targetdir_mp4", "") or "")
    subtitle_paths = []

    for raw_path in (
        getattr(cfg, "source_sub", None),
        getattr(cfg, "target_sub", None),
    ):
        if not raw_path:
            continue
        path = Path(raw_path)
        if path.exists() and str(path) not in subtitle_paths:
            subtitle_paths.append(str(path))

    if subtitle_type in BILINGUAL_SUBTITLE_TYPES:
        bilingual_path = Path(getattr(cfg, "target_dir", "")) / "shuang.srt"
        if bilingual_path.exists() and str(bilingual_path) not in subtitle_paths:
            subtitle_paths.append(str(bilingual_path))

    bilingual_order = None
    if subtitle_type in BILINGUAL_SUBTITLE_TYPES:
        bilingual_order = "source_target" if int(getattr(cfg, "output_srt", 2)) == 1 else "target_source"

    audio_paths = []
    raw_audio = getattr(cfg, "target_wav_output", None)
    if raw_audio and Path(raw_audio).exists():
        audio_paths.append(str(Path(raw_audio)))

    return {
        "subtitle_type": subtitle_type,
        "video_path": video_path,
        "subtitle_paths": subtitle_paths,
        "bilingual_order": bilingual_order,
        "soft_track_requires_player": subtitle_type in SOFT_SUBTITLE_TYPES,
        # Optional fields for the result panel; older receipts omit them.
        "audio_paths": audio_paths,
        "target_dir": str(getattr(cfg, "target_dir", "") or ""),
        "source_video": str(getattr(cfg, "name", "") or ""),
        "source_sub": str(getattr(cfg, "source_sub", "") or ""),
        "target_sub": str(getattr(cfg, "target_sub", "") or ""),
        "source_language_code": str(getattr(cfg, "source_language_code", "") or ""),
        "target_language_code": str(getattr(cfg, "target_language_code", "") or ""),
        "target_language": str(getattr(cfg, "target_language", "") or ""),
        "output_srt": int(getattr(cfg, "output_srt", 2) or 0),
        "video_autorate": bool(getattr(cfg, "video_autorate", False)),
    }
