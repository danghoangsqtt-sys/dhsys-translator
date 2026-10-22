import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QComboBox

from videotrans import recognition, translator, tts
from videotrans.configure._i18n import tr
from videotrans.ui.provider_visibility import (
    CUSTOM_ENDPOINT,
    LOCAL_MODEL,
    LOCAL_SERVICE,
    ONLINE_NO_KEY,
    PROVIDER_API,
    RECOGNITION,
    TRANSLATION,
    TTS,
    apply_combo_visibility,
    apply_menu_visibility,
    menu_action_visible,
    provider_access,
    refresh_registered_combos,
    register_provider_combo,
    visible_provider_ids,
)


app = QApplication.instance() or QApplication([])


def test_frozen_registry_ids_and_lengths_are_unchanged():
    assert tuple(translator.ID_NAME_DICT) == tuple(range(29))
    assert tuple(recognition.ID_NAME_DICT) == tuple(range(33))
    assert tuple(tts.ID_NAME_DICT) == tuple(range(38))
    assert len(translator.TRANSLASTE_NAME_LIST) == 29
    assert len(recognition.RECOGN_NAME_LIST) == 33
    assert len(tts.TTS_NAME_LIST) == 38


@pytest.mark.parametrize(
    ("kind", "names", "hidden_id"),
    (
        (TRANSLATION, translator.TRANSLASTE_NAME_LIST, translator.TENCENT_INDEX),
        (RECOGNITION, recognition.RECOGN_NAME_LIST, recognition.ZIJIE_RECOGN_MODEL),
        (TTS, tts.TTS_NAME_LIST, tts.DOUBAO2_TTS),
    ),
)
def test_combo_curated_mode_hides_rows_without_reindexing(kind, names, hidden_id):
    combo = QComboBox()
    combo.addItems(names)
    combo.setCurrentIndex(0)

    visible = apply_combo_visibility(combo, kind)

    assert combo.count() == len(names)
    assert combo.itemText(hidden_id) == names[hidden_id]
    assert hidden_id not in visible
    assert combo.view().isRowHidden(hidden_id)
    assert not combo.view().isRowHidden(0)


@pytest.mark.parametrize(
    ("kind", "names", "legacy_id"),
    (
        (TRANSLATION, translator.TRANSLASTE_NAME_LIST, translator.BAIDU_INDEX),
        (RECOGNITION, recognition.RECOGN_NAME_LIST, recognition.QWEN3ASR),
        (TTS, tts.TTS_NAME_LIST, tts.QWEN_TTS),
    ),
)
def test_selected_hidden_provider_remains_visible_and_selected(kind, names, legacy_id):
    combo = QComboBox()
    combo.addItems(names)
    combo.setCurrentIndex(legacy_id)

    visible = apply_combo_visibility(combo, kind)

    assert combo.currentIndex() == legacy_id
    assert legacy_id in visible
    assert not combo.view().isRowHidden(legacy_id)


@pytest.mark.parametrize(
    ("kind", "names"),
    (
        (TRANSLATION, translator.TRANSLASTE_NAME_LIST),
        (RECOGNITION, recognition.RECOGN_NAME_LIST),
        (TTS, tts.TTS_NAME_LIST),
    ),
)
def test_show_all_restores_every_original_row(kind, names):
    combo = QComboBox()
    combo.addItems(names)
    apply_combo_visibility(combo, kind)

    visible = apply_combo_visibility(combo, kind, show_all=True)

    assert visible == tuple(range(len(names)))
    assert all(not combo.view().isRowHidden(row) for row in range(len(names)))


def test_visibility_policy_has_expected_vietnam_global_defaults():
    translation_ids = visible_provider_ids(TRANSLATION)
    recognition_ids = visible_provider_ids(RECOGNITION)
    tts_ids = visible_provider_ids(TTS)

    assert translator.GOOGLE_INDEX in translation_ids
    assert translator.LOCALLLM_INDEX in translation_ids
    assert translator.TENCENT_INDEX not in translation_ids
    assert recognition.FASTER_WHISPER in recognition_ids
    assert recognition.HUGGINGFACE_ASR in recognition_ids
    assert recognition.ZIJIE_RECOGN_MODEL not in recognition_ids
    assert tts.EDGE_TTS in tts_ids
    assert tts.Supertonic_TTS in tts_ids
    assert tts.DOUBAO2_TTS not in tts_ids


def test_access_categories_distinguish_bundled_online_and_paid_api_paths():
    assert provider_access(RECOGNITION, recognition.FASTER_WHISPER).category == LOCAL_MODEL
    assert provider_access(TTS, tts.EDGE_TTS).category == ONLINE_NO_KEY
    assert provider_access(TRANSLATION, translator.CHATGPT_INDEX).category == PROVIDER_API
    assert provider_access(TTS, tts.TTS_API).category == CUSTOM_ENDPOINT
    assert provider_access(TTS, tts.EDGE_TTS).api_key_required is False
    assert provider_access(TRANSLATION, translator.CHATGPT_INDEX).provider_charge_possible is True


@pytest.mark.parametrize(
    ("kind", "names"),
    (
        (TRANSLATION, translator.TRANSLASTE_NAME_LIST),
        (RECOGNITION, recognition.RECOGN_NAME_LIST),
        (TTS, tts.TTS_NAME_LIST),
    ),
)
def test_every_provider_row_has_localized_cost_readiness_guidance(kind, names):
    combo = QComboBox()
    combo.addItems(names)

    apply_combo_visibility(combo, kind)

    for provider_id in range(len(names)):
        access = provider_access(kind, provider_id)
        assert access.category in {
            LOCAL_MODEL, ONLINE_NO_KEY, PROVIDER_API, LOCAL_SERVICE, CUSTOM_ENDPOINT,
        }
        assert combo.itemData(provider_id, Qt.ItemDataRole.ToolTipRole) == tr(
            access.guidance_key
        )


def test_settings_menu_policy_hides_china_focused_actions_but_can_restore_them():
    assert menu_action_visible(TRANSLATION, "chatgpt")
    assert not menu_action_visible(TRANSLATION, "deepl")
    assert not menu_action_visible(TRANSLATION, "deepseek")
    assert not menu_action_visible(TRANSLATION, "tencent")
    assert not menu_action_visible(RECOGNITION, "deepgram")
    assert not menu_action_visible(TTS, "elevenlabs")
    assert not menu_action_visible(TTS, "azuretts")
    assert not menu_action_visible(RECOGNITION, "zijierecognmodel")
    assert not menu_action_visible(TTS, "doubao2")
    assert menu_action_visible(TRANSLATION, "tencent", show_all=True)


def test_registered_open_combos_follow_one_show_all_refresh():
    combos = []
    for kind, names in (
        (TRANSLATION, translator.TRANSLASTE_NAME_LIST),
        (RECOGNITION, recognition.RECOGN_NAME_LIST),
        (TTS, tts.TTS_NAME_LIST),
    ):
        combo = QComboBox()
        combo.addItems(names)
        register_provider_combo(combo, kind, show_all=False)
        combos.append(combo)

    assert any(combo.view().isRowHidden(row) for combo in combos for row in range(combo.count()))

    refresh_registered_combos(show_all=True)

    assert all(
        not combo.view().isRowHidden(row)
        for combo in combos
        for row in range(combo.count())
    )


def test_generated_provider_menus_keep_actions_but_hide_and_restore_them(monkeypatch):
    from PySide6.QtWidgets import QMainWindow
    from videotrans.ui import _setup_menus
    from videotrans.ui.en import Ui_MainWindow

    class Params(dict):
        def getset_params(self, update):
            self.update(update)

    saved = Params(show_all_providers=False)
    monkeypatch.setattr(_setup_menus, "params", saved)

    class Window(QMainWindow, Ui_MainWindow):
        pass

    window = Window()
    window.setupUi(window)

    assert window.tencent in window.menu_Key.actions()
    assert window.tencent.isVisible() is False
    assert window.chatgpt.isVisible() is True
    assert window.deepl.isVisible() is False
    advanced = window.menu_provider_advanced.menuAction()
    assert window.show_all_providers in window.menu_provider_advanced.actions()
    for provider_menu in (window.menu_Key, window.menu_TTS, window.menu_RECOGN):
        assert advanced in provider_menu.actions()
        assert window.show_all_providers not in provider_menu.actions()

    window.show_all_providers.setChecked(True)

    assert saved["show_all_providers"] is True
    assert window.tencent.isVisible() is True
    assert window.zijierecognmodel.isVisible() is True
    assert window.doubao2.isVisible() is True
    assert window.deepl.isVisible() is True
    apply_menu_visibility(window, show_all=False)


PHASE8_CURATED = {
    TRANSLATION: {
        translator.GOOGLE_INDEX, translator.MICROSOFT_INDEX, translator.M2M100_INDEX,
        translator.CHATGPT_INDEX, translator.GEMINI_INDEX, translator.OPENROUTER_INDEX,
        translator.LOCALLLM_INDEX, translator.LITELLM_INDEX, translator.DEEPLX_INDEX,
        translator.LIBRE_INDEX, translator.TRANSAPI_INDEX,
    },
    RECOGNITION: {
        recognition.GOOGLE_SPEECH, recognition.OPENAI_API, recognition.GEMINI_SPEECH,
        recognition.OPENROUTER_API, recognition.FASTER_WHISPER, recognition.OPENAI_WHISPER,
        recognition.Whisper_CPP, recognition.Faster_Whisper_XXL, recognition.WHISPERX_API,
        recognition.PARAKEET, recognition.NEMOTRON_ASR, recognition.Omnilingual,
        recognition.HUGGINGFACE_ASR, recognition.WHISPER_NET, recognition.STT_API,
        recognition.CUSTOM_API,
    },
    TTS: {
        tts.EDGE_TTS, tts.G_TTS, tts.OPENAI_TTS, tts.GEMINI_TTS, tts.OPENROUTER_API,
        tts.F5_TTS, tts.OMNIVOICE_TTS, tts.PIPER_TTS, tts.CHATTERBOX_TTS,
        tts.Supertonic_TTS, tts.GPTSOVITS_TTS, tts.KOKORO_TTS, tts.TTS_API,
    },
}


@pytest.mark.parametrize("kind", (TRANSLATION, RECOGNITION, TTS))
def test_phase8_default_view_matches_vietnam_contract_exactly(kind):
    assert set(visible_provider_ids(kind)) == PHASE8_CURATED[kind]


@pytest.mark.parametrize(
    ("kind", "provider_id"),
    (
        (TRANSLATION, translator.DEEPSEEK_INDEX),
        (TRANSLATION, translator.AZUREGPT_INDEX),
        (TRANSLATION, translator.DEEPL_INDEX),
        (RECOGNITION, recognition.Deepgram),
        (RECOGNITION, recognition.ElevenLabs),
        (TTS, tts.ELEVENLABS_TTS),
        (TTS, tts.AZURE_TTS),
    ),
)
def test_phase8_moves_less_reachable_clouds_to_advanced(kind, provider_id):
    assert provider_id not in visible_provider_ids(kind)
    assert provider_id in visible_provider_ids(kind, show_all=True)


@pytest.mark.parametrize(
    ("kind", "names", "hidden_id"),
    (
        (TRANSLATION, translator.TRANSLASTE_NAME_LIST, translator.DEEPSEEK_INDEX),
        (RECOGNITION, recognition.RECOGN_NAME_LIST, recognition.Deepgram),
        (TTS, tts.TTS_NAME_LIST, tts.AZURE_TTS),
    ),
)
def test_hidden_selected_provider_is_labelled_and_label_is_restorable(kind, names, hidden_id):
    combo = QComboBox()
    combo.addItems(names)
    combo.setCurrentIndex(hidden_id)
    suffix = " " + tr("provider_hidden_suffix")

    apply_combo_visibility(combo, kind)
    apply_combo_visibility(combo, kind)

    assert combo.currentIndex() == hidden_id
    assert not combo.view().isRowHidden(hidden_id)
    assert combo.itemText(hidden_id) == names[hidden_id] + suffix

    apply_combo_visibility(combo, kind, show_all=True)

    assert combo.itemText(hidden_id) == names[hidden_id]
    assert all(combo.itemText(row) == names[row] for row in range(len(names)))


def test_curated_selection_gets_no_hidden_suffix():
    combo = QComboBox()
    combo.addItems(translator.TRANSLASTE_NAME_LIST)
    combo.setCurrentIndex(translator.GOOGLE_INDEX)

    apply_combo_visibility(combo, TRANSLATION)

    assert combo.itemText(translator.GOOGLE_INDEX) == translator.TRANSLASTE_NAME_LIST[translator.GOOGLE_INDEX]
