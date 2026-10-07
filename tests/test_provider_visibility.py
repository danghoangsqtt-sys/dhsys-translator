import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication, QComboBox

from videotrans import recognition, translator, tts
from videotrans.ui.provider_visibility import (
    CUSTOM_ENDPOINT,
    LOCAL_MODEL,
    ONLINE_NO_KEY,
    PROVIDER_API,
    RECOGNITION,
    TRANSLATION,
    TTS,
    apply_combo_visibility,
    menu_action_visible,
    provider_access,
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


def test_settings_menu_policy_hides_china_focused_actions_but_can_restore_them():
    assert menu_action_visible(TRANSLATION, "deepl")
    assert not menu_action_visible(TRANSLATION, "tencent")
    assert not menu_action_visible(RECOGNITION, "zijierecognmodel")
    assert not menu_action_visible(TTS, "doubao2")
    assert menu_action_visible(TRANSLATION, "tencent", show_all=True)

