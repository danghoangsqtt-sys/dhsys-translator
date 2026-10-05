"""Reversible provider presets layered over the frozen provider registries."""

from dataclasses import dataclass
from typing import Mapping

from videotrans import recognition, translator, tts


PROFILE_CUSTOM = "custom"
PROFILE_LOCAL = "local"
PROFILE_GEMINI = "gemini"


@dataclass(frozen=True)
class ProviderSelection:
    recogn_type: int
    translate_type: int
    tts_type: int

    def to_dict(self):
        return {
            "recogn_type": self.recogn_type,
            "translate_type": self.translate_type,
            "tts_type": self.tts_type,
        }


@dataclass(frozen=True)
class ProviderProfile:
    key: str
    label_key: str
    hint_key: str
    selection: ProviderSelection | None = None
    remote: bool = False


@dataclass(frozen=True)
class ProfileTransition:
    profile_key: str
    selection: ProviderSelection
    custom_backup: ProviderSelection | None


PROFILES = (
    ProviderProfile(
        PROFILE_LOCAL,
        "profile_local_label",
        "profile_local_hint",
        ProviderSelection(
            recognition.FASTER_WHISPER,
            translator.LOCALLLM_INDEX,
            tts.Supertonic_TTS,
        ),
    ),
    ProviderProfile(
        PROFILE_GEMINI,
        "profile_gemini_label",
        "profile_gemini_hint",
        ProviderSelection(
            recognition.GEMINI_SPEECH,
            translator.GEMINI_INDEX,
            tts.EDGE_TTS,
        ),
        remote=True,
    ),
    ProviderProfile(
        PROFILE_CUSTOM,
        "profile_custom_label",
        "profile_custom_hint",
    ),
)
PROFILE_BY_KEY = {profile.key: profile for profile in PROFILES}


def _valid_selection(value) -> ProviderSelection | None:
    if isinstance(value, ProviderSelection):
        selection = value
    elif isinstance(value, Mapping):
        try:
            selection = ProviderSelection(
                recogn_type=value["recogn_type"],
                translate_type=value["translate_type"],
                tts_type=value["tts_type"],
            )
        except (KeyError, TypeError):
            return None
    else:
        return None
    if type(selection.recogn_type) is not int or selection.recogn_type not in recognition.ID_NAME_DICT:
        return None
    if type(selection.translate_type) is not int or selection.translate_type not in translator.ID_NAME_DICT:
        return None
    if type(selection.tts_type) is not int or selection.tts_type not in tts.ID_NAME_DICT:
        return None
    return selection


def resolve_profile_transition(profile_key, current, active_profile, custom_backup):
    """Resolve one profile change while retaining the last explicit custom choice."""
    current = _valid_selection(current)
    if current is None:
        raise ValueError("Current provider selection is invalid")
    if profile_key not in PROFILE_BY_KEY:
        profile_key = PROFILE_CUSTOM
    backup = _valid_selection(custom_backup)
    if active_profile == PROFILE_CUSTOM and profile_key != PROFILE_CUSTOM:
        backup = current
    profile = PROFILE_BY_KEY[profile_key]
    if profile_key == PROFILE_CUSTOM:
        selection = backup or current
    else:
        selection = profile.selection
    return ProfileTransition(profile_key, selection, backup)
