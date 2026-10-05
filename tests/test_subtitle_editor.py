import json
from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QAbstractItemView, QApplication

from videotrans.component import onlyone_set_recogn, onlyone_set_recogn2


app = QApplication.instance() or QApplication([])


SRT_TEXT = "1\n00:00:00,000 --> 00:00:01,500\nOriginal subtitle\n"


class _ParentDouble:
    screen_size = (1200, 800)
    height = 800


class _TimerStub:
    @staticmethod
    def singleShot(delay, callback):
        # Skip the constructor's delayed load, but keep zero-delay row batches synchronous.
        if delay == 0:
            callback()


@pytest.fixture(params=[
    (onlyone_set_recogn, onlyone_set_recogn.EditRecognResultDialog, "onlyone_source_sub"),
    (onlyone_set_recogn2, onlyone_set_recogn2.EditRecognResultDialog2, "onlyone_target_sub"),
])
def subtitle_dialog(request, monkeypatch, tmp_path):
    module, dialog_class, app_cfg_attr = request.param
    subtitle_path = tmp_path / f"{app_cfg_attr}.srt"
    subtitle_path.write_text(SRT_TEXT, encoding="utf-8")

    monkeypatch.setattr(module, "QTimer", _TimerStub)
    monkeypatch.setattr(dialog_class, "_play_segment", lambda *_args: None)
    monkeypatch.setattr(module.app_cfg, app_cfg_attr, str(subtitle_path))

    dialog = dialog_class(parent=_ParentDouble())
    dialog.load_table()
    yield dialog, subtitle_path
    dialog.deleteLater()


def test_both_subtitle_dialogs_are_focusable_selectable_and_editable(subtitle_dialog):
    dialog, _ = subtitle_dialog

    assert dialog.table.focusPolicy() == Qt.StrongFocus
    assert dialog.table.selectionMode() == QAbstractItemView.SingleSelection
    assert dialog.table.selectionBehavior() == QAbstractItemView.SelectItems
    assert dialog.table.editTriggers() & QAbstractItemView.DoubleClicked
    assert dialog.table.editTriggers() & QAbstractItemView.SelectedClicked
    assert dialog.table.editTriggers() & QAbstractItemView.EditKeyPressed
    assert dialog.table.editTriggers() & QAbstractItemView.AnyKeyPressed
    assert dialog.table.item(0, 5).flags() & Qt.ItemIsEditable
    assert dialog.timer is None
    assert dialog.stop_button is None


def test_initial_render_is_clean_and_user_edit_marks_dialog_dirty(subtitle_dialog):
    dialog, _ = subtitle_dialog

    assert dialog.has_unsaved_changes is False
    assert dialog.dirty_label.property("dirty") is False

    dialog.table.item(0, 5).setText("Edited subtitle")

    assert dialog.has_unsaved_changes is True
    assert dialog.dirty_label.property("dirty") is True


def test_save_writes_edited_srt_for_both_dialogs(subtitle_dialog):
    dialog, subtitle_path = subtitle_dialog
    dialog.table.item(0, 5).setText("Saved subtitle")

    dialog.save_and_close()

    saved = subtitle_path.read_text(encoding="utf-8")
    assert "Saved subtitle" in saved
    assert "Original subtitle" not in saved
    assert dialog.has_unsaved_changes is False


def test_continue_without_saving_preserves_original_file(subtitle_dialog):
    dialog, subtitle_path = subtitle_dialog
    before = subtitle_path.read_bytes()
    dialog.table.item(0, 5).setText("Discarded subtitle")

    dialog.save_and_close2()

    assert subtitle_path.read_bytes() == before


def test_subtitle_editor_uses_light_contrast_tokens_and_localized_status_keys():
    repo_root = Path(__file__).resolve().parents[1]
    mixin_source = (repo_root / "videotrans/component/_danspmixin.py").read_text(encoding="utf-8")
    qss = (repo_root / "videotrans/styles/light.qss").read_text(encoding="utf-8")

    assert "#17211c" in mixin_source
    assert "#dcede4" in mixin_source
    assert "#cccccc" not in mixin_source
    assert "QLabel#subtitleDirtyState" in qss
    assert "QPushButton#subtitleSaveButton" in qss

    for locale in ("en_US", "vi_VN"):
        catalog = json.loads(
            (repo_root / f"videotrans/language/{locale}.json").read_text(encoding="utf-8")
        )
        assert catalog["Review subtitles and save when ready"]
        assert catalog["Unsaved subtitle changes"]
        assert catalog["Could not save subtitle file"]
