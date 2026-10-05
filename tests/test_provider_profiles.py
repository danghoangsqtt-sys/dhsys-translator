import socket

import pytest

from videotrans import recognition, translator, tts
from videotrans.configure._languages_dict import EDGE_LANGUANGES_CODE
from videotrans.mainwin import main_win
from videotrans.ui.provider_profiles import (
    ENDPOINT_LOCAL_NETWORK,
    ENDPOINT_LOOPBACK,
    ENDPOINT_PUBLIC,
    ENDPOINT_UNKNOWN,
    PROFILE_CUSTOM,
    PROFILE_GEMINI,
    PROFILE_LOCAL,
    PROFILE_BY_KEY,
    ProviderSelection,
    classify_endpoint,
    profile_policy,
    resolve_profile_transition,
)


def test_profile_presets_use_existing_provider_ids_without_renumbering():
    current = ProviderSelection(recogn_type=4, translate_type=10, tts_type=7)

    local = resolve_profile_transition(PROFILE_LOCAL, current, PROFILE_CUSTOM, None)
    gemini = resolve_profile_transition(PROFILE_GEMINI, local.selection, PROFILE_LOCAL, local.custom_backup)

    assert local.selection == ProviderSelection(
        recogn_type=recognition.FASTER_WHISPER,
        translate_type=translator.LOCALLLM_INDEX,
        tts_type=tts.Supertonic_TTS,
    )
    assert gemini.selection == ProviderSelection(
        recogn_type=recognition.GEMINI_SPEECH,
        translate_type=translator.GEMINI_INDEX,
        tts_type=tts.EDGE_TTS,
    )
    assert local.selection.recogn_type in recognition.ID_NAME_DICT
    assert local.selection.translate_type in translator.ID_NAME_DICT
    assert local.selection.tts_type in tts.ID_NAME_DICT
    assert gemini.selection.recogn_type in recognition.ID_NAME_DICT
    assert gemini.selection.translate_type in translator.ID_NAME_DICT
    assert gemini.selection.tts_type in tts.ID_NAME_DICT
    assert PROFILE_BY_KEY[PROFILE_LOCAL].remote is False
    assert PROFILE_BY_KEY[PROFILE_GEMINI].remote is True
    assert recognition.ID_NAME_DICT[local.selection.recogn_type].key_name is None
    assert tts.ID_NAME_DICT[local.selection.tts_type].key_name is None
    assert translator.ID_NAME_DICT[local.selection.translate_type].key_name == "localllm_api"


def test_frozen_provider_registries_and_chinese_media_codes_remain_unchanged():
    assert tuple(translator.ID_NAME_DICT) == tuple(range(29))
    assert tuple(recognition.ID_NAME_DICT) == tuple(range(33))
    assert tuple(tts.ID_NAME_DICT) == tuple(range(38))
    assert {"zh-cn", "zh-tw", "yue"} <= set(EDGE_LANGUANGES_CODE)


@pytest.mark.parametrize(
    ("endpoint", "expected"),
    (
        ("http://localhost:8000/v1", ENDPOINT_LOOPBACK),
        ("127.0.0.1:8000/v1", ENDPOINT_LOOPBACK),
        ("http://127.23.45.67:9000", ENDPOINT_LOOPBACK),
        ("http://[::1]:8000/v1", ENDPOINT_LOOPBACK),
        ("http://192.168.1.20:8000/v1", ENDPOINT_LOCAL_NETWORK),
        ("http://10.20.30.40:8000/v1", ENDPOINT_LOCAL_NETWORK),
        ("https://api.example.com/v1", ENDPOINT_PUBLIC),
        ("https://8.8.8.8/v1", ENDPOINT_PUBLIC),
        ("", ENDPOINT_UNKNOWN),
        ("local-llm", ENDPOINT_UNKNOWN),
        ("not a url", ENDPOINT_UNKNOWN),
    ),
)
def test_endpoint_classification_is_deterministic_and_offline(monkeypatch, endpoint, expected):
    def fail_dns(*args, **kwargs):
        raise AssertionError("endpoint classification must not perform DNS/network I/O")

    monkeypatch.setattr(socket, "getaddrinfo", fail_dns)

    assert classify_endpoint(endpoint) == expected


def test_profile_policy_only_marks_local_profile_ready_for_loopback_endpoint():
    ready = profile_policy(PROFILE_LOCAL, "http://127.0.0.1:8000/v1")
    lan = profile_policy(PROFILE_LOCAL, "http://192.168.1.20:8000/v1")
    public = profile_policy(PROFILE_LOCAL, "https://api.example.com/v1")
    missing = profile_policy(PROFILE_LOCAL, "")
    gemini = profile_policy(PROFILE_GEMINI, "")
    custom = profile_policy(PROFILE_CUSTOM, "")

    assert ready.local_only_ready is True
    assert ready.off_device is False
    assert ready.endpoint_classification == ENDPOINT_LOOPBACK

    assert lan.local_only_ready is False
    assert lan.off_device is True
    assert public.local_only_ready is False
    assert public.off_device is True
    assert missing.local_only_ready is False
    assert missing.off_device is None

    assert gemini.off_device is True
    assert gemini.local_only_ready is False
    assert custom.off_device is None
    assert custom.local_only_ready is False


def test_profile_switch_restores_the_prior_custom_provider_selection():
    custom = ProviderSelection(recogn_type=8, translate_type=10, tts_type=29)

    local = resolve_profile_transition(PROFILE_LOCAL, custom, PROFILE_CUSTOM, None)
    gemini = resolve_profile_transition(PROFILE_GEMINI, local.selection, PROFILE_LOCAL, local.custom_backup)
    restored = resolve_profile_transition(PROFILE_CUSTOM, gemini.selection, PROFILE_GEMINI, gemini.custom_backup)

    assert local.custom_backup == custom
    assert gemini.custom_backup == custom
    assert restored.selection == custom
    assert restored.custom_backup == custom


def test_invalid_saved_custom_backup_falls_back_without_changing_current_ids():
    current = ProviderSelection(recogn_type=2, translate_type=3, tts_type=4)

    restored = resolve_profile_transition(
        PROFILE_CUSTOM,
        current,
        PROFILE_GEMINI,
        {"recogn_type": "bad", "translate_type": 999},
    )

    assert restored.selection == current


def test_main_window_profile_application_persists_exact_ids_and_restores_custom(monkeypatch):
    class Params(dict):
        def getset_params(self, update):
            self.update(update)

    class Combo:
        def __init__(self, value):
            self.value = value

        def currentIndex(self):
            return self.value

        def setCurrentIndex(self, value):
            self.value = value

    class Shell:
        def __init__(self):
            self.profile = None

        def set_provider_profile(self, profile):
            self.profile = profile

    saved = Params(
        provider_profile=PROFILE_CUSTOM,
        provider_profile_custom={},
        recogn_type=8,
        translate_type=10,
        tts_type=29,
        gemini_key="keep-secret",
        openrouter_key="keep-custom-secret",
    )
    monkeypatch.setattr(main_win, "params", saved)
    harness = type("Harness", (), {})()
    harness.recogn_type = Combo(8)
    harness.translate_type = Combo(10)
    harness.tts_type = Combo(29)
    harness.workspace_shell = Shell()
    harness.current_provider_profile = lambda: main_win.MainWindow.current_provider_profile(harness)

    main_win.MainWindow.apply_provider_profile(harness, PROFILE_LOCAL)
    assert (saved["recogn_type"], saved["translate_type"], saved["tts_type"]) == (
        recognition.FASTER_WHISPER,
        translator.LOCALLLM_INDEX,
        tts.Supertonic_TTS,
    )
    assert saved["provider_profile_custom"] == {
        "recogn_type": 8,
        "translate_type": 10,
        "tts_type": 29,
    }
    assert saved["gemini_key"] == "keep-secret"
    assert saved["openrouter_key"] == "keep-custom-secret"

    main_win.MainWindow.apply_provider_profile(harness, PROFILE_GEMINI)
    main_win.MainWindow.apply_provider_profile(harness, PROFILE_CUSTOM)

    assert (saved["recogn_type"], saved["translate_type"], saved["tts_type"]) == (8, 10, 29)
    assert harness.workspace_shell.profile == PROFILE_CUSTOM
