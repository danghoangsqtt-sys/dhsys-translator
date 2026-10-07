"""Reversible provider presets layered over the frozen provider registries."""

from dataclasses import dataclass
from ipaddress import ip_address
from typing import Mapping
from urllib.parse import urlsplit

from videotrans import recognition, translator, tts


PROFILE_CUSTOM = "custom"
PROFILE_NO_KEY = "no_key"
PROFILE_LOCAL = "local"
PROFILE_GEMINI = "gemini"

ENDPOINT_LOOPBACK = "loopback"
ENDPOINT_LOCAL_NETWORK = "local-network"
ENDPOINT_PUBLIC = "public"
ENDPOINT_UNKNOWN = "unknown"


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


@dataclass(frozen=True)
class ProfilePolicy:
    profile_key: str
    endpoint_classification: str
    off_device: bool | None
    local_only_ready: bool
    summary_key: str


PROFILES = (
    ProviderProfile(
        PROFILE_NO_KEY,
        "profile_no_key_label",
        "profile_no_key_hint",
        ProviderSelection(
            recognition.FASTER_WHISPER,
            translator.GOOGLE_INDEX,
            tts.EDGE_TTS,
        ),
        remote=True,
    ),
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


def _endpoint_host(endpoint) -> str | None:
    if not isinstance(endpoint, str):
        return None
    value = endpoint.strip()
    if not value or any(char.isspace() for char in value):
        return None

    try:
        return str(ip_address(value.strip("[]")))
    except ValueError:
        pass

    candidate = value if "://" in value else f"//{value}"
    try:
        parsed = urlsplit(candidate)
        if parsed.scheme and parsed.scheme.lower() not in {"http", "https"}:
            return None
        host = parsed.hostname
    except ValueError:
        return None
    if not host:
        return None
    return host.rstrip(".").lower()


def classify_endpoint(endpoint) -> str:
    """Classify an endpoint without DNS lookup or any network I/O."""
    host = _endpoint_host(endpoint)
    if not host:
        return ENDPOINT_UNKNOWN
    if host == "localhost":
        return ENDPOINT_LOOPBACK

    try:
        address = ip_address(host)
    except ValueError:
        if host.endswith(".local"):
            return ENDPOINT_LOCAL_NETWORK
        labels = host.split(".")
        if len(labels) > 1 and all(
            label and label[0].isalnum() and label[-1].isalnum()
            and all(char.isalnum() or char == "-" for char in label)
            for label in labels
        ):
            return ENDPOINT_PUBLIC
        return ENDPOINT_UNKNOWN

    if address.is_loopback:
        return ENDPOINT_LOOPBACK
    if address.is_unspecified or address.is_multicast:
        return ENDPOINT_UNKNOWN
    if address.is_private or address.is_link_local:
        return ENDPOINT_LOCAL_NETWORK
    if address.is_global:
        return ENDPOINT_PUBLIC
    return ENDPOINT_UNKNOWN


def profile_policy(profile_key, localllm_api="") -> ProfilePolicy:
    """Return privacy/readiness policy without mutating provider state."""
    if profile_key == PROFILE_LOCAL:
        classification = classify_endpoint(localllm_api)
        if classification == ENDPOINT_LOOPBACK:
            return ProfilePolicy(
                PROFILE_LOCAL,
                classification,
                off_device=False,
                local_only_ready=True,
                summary_key="profile_local_policy_ready",
            )
        if classification in {ENDPOINT_LOCAL_NETWORK, ENDPOINT_PUBLIC}:
            return ProfilePolicy(
                PROFILE_LOCAL,
                classification,
                off_device=True,
                local_only_ready=False,
                summary_key="profile_local_policy_off_device",
            )
        return ProfilePolicy(
            PROFILE_LOCAL,
            classification,
            off_device=None,
            local_only_ready=False,
            summary_key="profile_local_policy_unknown",
        )

    if profile_key == PROFILE_NO_KEY:
        return ProfilePolicy(
            PROFILE_NO_KEY,
            ENDPOINT_PUBLIC,
            off_device=True,
            local_only_ready=False,
            summary_key="profile_no_key_policy_remote",
        )

    if profile_key == PROFILE_GEMINI:
        return ProfilePolicy(
            PROFILE_GEMINI,
            ENDPOINT_PUBLIC,
            off_device=True,
            local_only_ready=False,
            summary_key="profile_gemini_policy_remote",
        )

    return ProfilePolicy(
        PROFILE_CUSTOM,
        ENDPOINT_UNKNOWN,
        off_device=None,
        local_only_ready=False,
        summary_key="profile_custom_policy_unknown",
    )


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
