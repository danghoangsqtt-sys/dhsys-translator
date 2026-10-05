from videotrans import recognition, translator, tts
from videotrans.mainwin import main_win
from videotrans.ui.provider_profiles import (
    PROFILE_CUSTOM,
    PROFILE_GEMINI,
    PROFILE_LOCAL,
    ProviderSelection,
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

    main_win.MainWindow.apply_provider_profile(harness, PROFILE_GEMINI)
    main_win.MainWindow.apply_provider_profile(harness, PROFILE_CUSTOM)

    assert (saved["recogn_type"], saved["translate_type"], saved["tts_type"]) == (8, 10, 29)
    assert harness.workspace_shell.profile == PROFILE_CUSTOM
