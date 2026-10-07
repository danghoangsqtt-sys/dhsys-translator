"""Presentation policy for the provider-heavy desktop surfaces.

Provider IDs are persisted as combo-box indexes throughout the application.  This
module therefore hides rows in the existing model instead of constructing shorter
lists.  Availability, imports and credentials remain owned by the provider
registries; this policy only decides what a typical Viet Nam/global user sees first.
"""

from dataclasses import dataclass
from types import MappingProxyType
from weakref import ref

from videotrans import recognition, translator, tts


TRANSLATION = "translation"
RECOGNITION = "recognition"
TTS = "tts"

LOCAL_MODEL = "local_model"
ONLINE_NO_KEY = "online_no_key"
PROVIDER_API = "provider_api"
LOCAL_SERVICE = "local_service"
CUSTOM_ENDPOINT = "custom_endpoint"


@dataclass(frozen=True)
class ProviderAccess:
    """Stable readiness facts; numeric prices and temporary quotas stay out of code."""

    category: str
    api_key_required: bool
    provider_charge_possible: bool
    guidance_key: str


ACCESS_BY_CATEGORY = MappingProxyType({
    LOCAL_MODEL: ProviderAccess(
        LOCAL_MODEL, False, False, "provider_access_local_model"
    ),
    ONLINE_NO_KEY: ProviderAccess(
        ONLINE_NO_KEY, False, False, "provider_access_online_no_key"
    ),
    PROVIDER_API: ProviderAccess(
        PROVIDER_API, True, True, "provider_access_provider_api"
    ),
    LOCAL_SERVICE: ProviderAccess(
        LOCAL_SERVICE, False, False, "provider_access_local_service"
    ),
    CUSTOM_ENDPOINT: ProviderAccess(
        CUSTOM_ENDPOINT, False, True, "provider_access_custom_endpoint"
    ),
})


# Keep the default surfaces intentionally compact.  These providers are broadly
# useful internationally, work well with Vietnamese, or provide a practical local
# or user-controlled path.  Providers outside these sets are still fully available
# through the show-all control.
CURATED_PROVIDER_IDS = MappingProxyType({
    TRANSLATION: frozenset({
        translator.GOOGLE_INDEX,
        translator.MICROSOFT_INDEX,
        translator.M2M100_INDEX,
        translator.CHATGPT_INDEX,
        translator.DEEPSEEK_INDEX,
        translator.GEMINI_INDEX,
        translator.AZUREGPT_INDEX,
        translator.LOCALLLM_INDEX,
        translator.OPENROUTER_INDEX,
        translator.DEEPL_INDEX,
        translator.DEEPLX_INDEX,
        translator.LIBRE_INDEX,
        translator.TRANSAPI_INDEX,
        translator.LITELLM_INDEX,
    }),
    RECOGNITION: frozenset({
        recognition.FASTER_WHISPER,
        recognition.OPENAI_WHISPER,
        recognition.NEMOTRON_ASR,
        recognition.Omnilingual,
        recognition.HUGGINGFACE_ASR,
        recognition.Whisper_CPP,
        recognition.OPENAI_API,
        recognition.GEMINI_SPEECH,
        recognition.Faster_Whisper_XXL,
        recognition.WHISPERX_API,
        recognition.PARAKEET,
        recognition.ElevenLabs,
        recognition.GOOGLE_SPEECH,
        recognition.Deepgram,
        recognition.STT_API,
        recognition.WHISPER_NET,
        recognition.CUSTOM_API,
        recognition.OPENROUTER_API,
    }),
    TTS: frozenset({
        tts.EDGE_TTS,
        tts.F5_TTS,
        tts.OMNIVOICE_TTS,
        tts.PIPER_TTS,
        tts.CHATTERBOX_TTS,
        tts.Supertonic_TTS,
        tts.GPTSOVITS_TTS,
        tts.OPENAI_TTS,
        tts.GEMINI_TTS,
        tts.ELEVENLABS_TTS,
        tts.G_TTS,
        tts.KOKORO_TTS,
        tts.AZURE_TTS,
        tts.TTS_API,
        tts.OPENROUTER_API,
    }),
})


CURATED_MENU_ACTIONS = MappingProxyType({
    TRANSLATION: frozenset({
        "deepseek", "chatgpt", "gemini", "localllm", "azure",
        "openrouter", "litellm", "deepl", "deeplx", "libre", "transapi",
    }),
    RECOGNITION: frozenset({
        "openairecognapi", "parakeet", "whisperxapi", "deepgram", "xxl",
        "sttapi", "recognapi",
    }),
    TTS: frozenset({
        "refaudio", "openaitts", "elevenlabs", "azuretts", "gptsovits",
        "chatterbox", "kokoro", "clone", "ttsapi",
    }),
})


_REGISTRIES = MappingProxyType({
    TRANSLATION: translator.ID_NAME_DICT,
    RECOGNITION: recognition.ID_NAME_DICT,
    TTS: tts.ID_NAME_DICT,
})

_ACTIVE_COMBOS = []

_CATEGORY_OVERRIDES = MappingProxyType({
    TRANSLATION: {
        LOCAL_MODEL: {translator.M2M100_INDEX, translator.HYMT2_INDEX},
        ONLINE_NO_KEY: {translator.GOOGLE_INDEX, translator.MICROSOFT_INDEX},
        LOCAL_SERVICE: {
            translator.LOCALLLM_INDEX, translator.DEEPLX_INDEX,
            translator.LIBRE_INDEX, translator.LITELLM_INDEX,
        },
        CUSTOM_ENDPOINT: {translator.TRANSAPI_INDEX},
    },
    RECOGNITION: {
        LOCAL_MODEL: {
            recognition.FASTER_WHISPER, recognition.OPENAI_WHISPER,
            recognition.QWENASR, recognition.FUNASR_CN,
            recognition.NEMOTRON_ASR, recognition.FIREREDASR,
            recognition.DOLPHIN, recognition.Omnilingual,
            recognition.HUGGINGFACE_ASR, recognition.MOSS_DIARIZE,
            recognition.VIBEVOICE_ASR, recognition.Whisper_CPP,
            recognition.Faster_Whisper_XXL, recognition.WHISPER_NET,
        },
        ONLINE_NO_KEY: {recognition.GOOGLE_SPEECH},
        LOCAL_SERVICE: {
            recognition.WHISPERX_API, recognition.PARAKEET, recognition.STT_API,
        },
        CUSTOM_ENDPOINT: {recognition.CUSTOM_API},
    },
    TTS: {
        LOCAL_MODEL: set(range(tts.QWEN3LOCAL_TTS, tts.HIGGS_AUDIO_TTS + 1)),
        ONLINE_NO_KEY: {tts.EDGE_TTS, tts.G_TTS},
        LOCAL_SERVICE: {
            tts.INDEX_TTS, tts.GPTSOVITS_TTS, tts.COSYVOICE_TTS,
            tts.VOXCPM_TTS, tts.FIRERED3_TTS, tts.CHATTTS, tts.SPARK_TTS,
            tts.KOKORO_TTS, tts.FISHTTS, tts.CLONE_VOICE_TTS,
        },
        CUSTOM_ENDPOINT: {tts.TTS_API},
    },
})


def _validate_kind(kind: str):
    if kind not in _REGISTRIES:
        raise ValueError(f"Unknown provider kind: {kind}")


def provider_access(kind: str, provider_id: int) -> ProviderAccess:
    """Return deterministic access/cost guidance for one frozen provider ID."""
    _validate_kind(kind)
    if provider_id not in _REGISTRIES[kind]:
        raise ValueError(f"Unknown {kind} provider ID: {provider_id}")
    for category, provider_ids in _CATEGORY_OVERRIDES[kind].items():
        if provider_id in provider_ids:
            return ACCESS_BY_CATEGORY[category]
    return ACCESS_BY_CATEGORY[PROVIDER_API]


def visible_provider_ids(kind: str, *, show_all: bool = False, selected_id: int | None = None):
    """Return visible IDs while retaining a selected legacy/advanced provider."""
    _validate_kind(kind)
    registry_ids = tuple(_REGISTRIES[kind])
    if show_all:
        return registry_ids
    visible = set(CURATED_PROVIDER_IDS[kind])
    if selected_id in _REGISTRIES[kind]:
        visible.add(selected_id)
    return tuple(provider_id for provider_id in registry_ids if provider_id in visible)


def apply_combo_visibility(combo, kind: str, *, show_all: bool = False):
    """Hide model rows in place and return the IDs that remain visible."""
    _validate_kind(kind)
    registry_ids = tuple(_REGISTRIES[kind])
    if combo.count() != len(registry_ids):
        raise ValueError(
            f"{kind} combo has {combo.count()} rows; expected {len(registry_ids)}"
        )
    selected_id = combo.currentIndex()
    visible = set(visible_provider_ids(
        kind, show_all=show_all, selected_id=selected_id
    ))
    view = combo.view()
    for provider_id in registry_ids:
        view.setRowHidden(provider_id, provider_id not in visible)
    return tuple(provider_id for provider_id in registry_ids if provider_id in visible)


def register_provider_combo(combo, kind: str, *, show_all: bool = False):
    """Track an open desktop combo so the global show-all toggle can refresh it."""
    _validate_kind(kind)
    live = []
    found = False
    for combo_ref, registered_kind in _ACTIVE_COMBOS:
        candidate = combo_ref()
        if candidate is None:
            continue
        live.append((combo_ref, registered_kind))
        if candidate is combo:
            found = True
    _ACTIVE_COMBOS[:] = live
    if not found:
        _ACTIVE_COMBOS.append((ref(combo), kind))
    return apply_combo_visibility(combo, kind, show_all=show_all)


def refresh_registered_combos(*, show_all: bool = False):
    """Refresh every currently open combo; discard closed Qt wrappers safely."""
    live = []
    for combo_ref, kind in _ACTIVE_COMBOS:
        combo = combo_ref()
        if combo is None:
            continue
        try:
            apply_combo_visibility(combo, kind, show_all=show_all)
        except RuntimeError:
            continue
        live.append((combo_ref, kind))
    _ACTIVE_COMBOS[:] = live


def apply_menu_visibility(owner, *, show_all: bool = False):
    """Apply the same policy to registered provider-setting QAction objects."""
    for kind, actions in getattr(owner, "_provider_actions_by_kind", {}).items():
        for action in actions:
            action.setVisible(menu_action_visible(
                kind, action.objectName(), show_all=show_all
            ))


def menu_action_visible(kind: str, action_name: str, *, show_all: bool = False) -> bool:
    _validate_kind(kind)
    return show_all or action_name in CURATED_MENU_ACTIONS[kind]
