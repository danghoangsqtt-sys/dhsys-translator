"""Purpose presets for wizard step 1: pure mappings onto existing settings."""

from dataclasses import dataclass
from typing import Optional

PURPOSE_DUB_SUBTITLES = "dub_subtitles"
PURPOSE_SUBTITLES_ONLY = "subtitles_only"
PURPOSE_SRT_ONLY = "srt_only"

PURPOSES = (PURPOSE_DUB_SUBTITLES, PURPOSE_SUBTITLES_ONLY, PURPOSE_SRT_ONLY)

# Existing app modes from mainwin/_actions_base_mode.py.
APP_MODE_STANDARD = "biaozhun"
APP_MODE_EXTRACT = "tiqu"

# Persisted subtitle_type values (task/subtitle_output.SUBTITLE_TYPE_KEYS).
SUBTITLE_NONE = 0
SUBTITLE_HARD = 1


@dataclass(frozen=True)
class PurposeSettings:
    app_mode: str
    dubbing: bool
    subtitle_type: Optional[int]  # None leaves the subtitle control untouched
    needs_target_language: bool


def purpose_settings(purpose: str, current_subtitle_type: int = SUBTITLE_HARD) -> PurposeSettings:
    """Map a purpose to existing settings without touching any widget or file."""
    keep_or_hard = current_subtitle_type if current_subtitle_type and current_subtitle_type > SUBTITLE_NONE else SUBTITLE_HARD
    if purpose == PURPOSE_SRT_ONLY:
        return PurposeSettings(APP_MODE_EXTRACT, False, None, False)
    if purpose == PURPOSE_SUBTITLES_ONLY:
        return PurposeSettings(APP_MODE_STANDARD, False, keep_or_hard, True)
    return PurposeSettings(APP_MODE_STANDARD, True, keep_or_hard, True)


def purpose_for(app_mode: str, voice_role: str) -> str:
    """Best matching purpose for the current classic settings."""
    if app_mode == APP_MODE_EXTRACT:
        return PURPOSE_SRT_ONLY
    if not voice_role or voice_role == "No":
        return PURPOSE_SUBTITLES_ONLY
    return PURPOSE_DUB_SUBTITLES
