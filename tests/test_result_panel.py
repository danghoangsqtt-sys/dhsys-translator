import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from pathlib import Path
from types import SimpleNamespace

from PySide6.QtCore import QEvent, QUrl, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QApplication, QWidget

from videotrans.configure._i18n import tr
from videotrans.ui.result_panel import (
    ResultDialog,
    ResultPanel,
    format_duration,
    format_size,
    receipt_files,
    receipt_folder,
)

app = QApplication.instance() or QApplication([])


def _receipt(tmp_path, *, video=True, extra=True):
    out = tmp_path / "_video_out"
    out.mkdir()
    video_path = out / "clip-vi.mp4"
    if video:
        video_path.write_bytes(b"\0" * 2048)
    vi = out / "vi.srt"
    vi.write_text("1\n00:00:00,000 --> 00:00:01,000\nXin chào\n", encoding="utf-8")
    receipt = {
        "subtitle_type": 1,
        "video_path": str(video_path),
        "subtitle_paths": [str(vi), str(vi)],
        "bilingual_order": None,
        "soft_track_requires_player": False,
    }
    if extra:
        audio = out / "vi.m4a"
        audio.write_bytes(b"\0" * 10)
        receipt["audio_paths"] = [str(audio)]
        receipt["target_dir"] = str(out)
    return receipt


def _panel(urls=None):
    opened = [] if urls is None else urls
    return ResultPanel(open_url=lambda url: opened.append(url) or True), opened


def test_format_helpers():
    assert format_duration(0) == "0:00"
    assert format_duration(65_400) == "1:05"
    assert format_duration(3_725_000) == "1:02:05"
    assert format_size(512) == "512 B"
    assert format_size(2048) == "2.0 KB"
    assert format_size(5 * 1024 * 1024) == "5.0 MB"


def test_receipt_files_are_ordered_and_deduplicated(tmp_path):
    receipt = _receipt(tmp_path)
    names = [path.name for path in receipt_files(receipt)]
    assert names == ["clip-vi.mp4", "vi.srt", "vi.m4a"]
    assert receipt_folder(receipt).name == "_video_out"


def test_loads_existing_receipt_with_files_and_enabled_actions(tmp_path):
    panel, _ = _panel()
    panel.load_receipt(_receipt(tmp_path))

    assert panel.title.text() == "clip-vi.mp4"
    assert panel.files.count() == 3
    assert "2.0 KB" in panel.files.item(0).text()
    assert panel.play_button.isEnabled()
    assert panel.open_folder_button.isEnabled()
    assert panel.open_external_button.isEnabled()
    assert panel.message.isHidden()
    assert panel.selector.isHidden()
    assert panel.player.source().toLocalFile().endswith("clip-vi.mp4")
    panel.close()


def test_missing_video_shows_message_and_disables_playback(tmp_path):
    panel, _ = _panel()
    panel.load_receipt(_receipt(tmp_path, video=False))

    assert not panel.message.isHidden()
    assert tr("result_video_missing") in panel.message.text()
    assert not panel.play_button.isEnabled()
    assert not panel.open_external_button.isEnabled()
    missing = panel.files.item(0)
    assert tr("result_file_missing") in missing.text()
    assert not (missing.flags() & Qt.ItemFlag.ItemIsEnabled)
    assert panel.player.source().isEmpty()


def test_legacy_receipt_without_optional_fields_still_loads(tmp_path):
    receipt = _receipt(tmp_path, extra=False)
    panel, opened = _panel()
    panel.load_receipt(receipt)

    assert panel.files.count() == 2
    panel.open_folder()
    assert opened == [QUrl.fromLocalFile(str(tmp_path / "_video_out"))]


def test_actions_open_folder_external_and_file(tmp_path):
    receipt = _receipt(tmp_path)
    panel, opened = _panel()
    panel.load_receipt(receipt)

    panel.open_folder()
    panel.open_external()
    panel._open_file_item(panel.files.item(1))

    assert [url.toLocalFile() for url in opened] == [
        QUrl.fromLocalFile(receipt["target_dir"]).toLocalFile(),
        QUrl.fromLocalFile(receipt["video_path"]).toLocalFile(),
        QUrl.fromLocalFile(receipt["subtitle_paths"][0]).toLocalFile(),
    ]


def test_translate_another_releases_media_and_emits(tmp_path):
    panel, _ = _panel()
    panel.load_receipt(_receipt(tmp_path))
    fired = []
    panel.translate_another.connect(lambda: fired.append(True))

    panel.translate_another_button.click()

    assert fired == [True]
    assert panel.player.source().isEmpty()


def test_batch_receipts_show_selector_and_switch_video(tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    first = _receipt(tmp_path / "a")
    second = _receipt(tmp_path / "b")
    second_video = tmp_path / "b" / "_video_out" / "clip-vi.mp4"
    renamed = second_video.with_name("other-vi.mp4")
    second_video.rename(renamed)
    second["video_path"] = str(renamed)

    panel, _ = _panel()
    panel.load_receipts([first, second])

    assert not panel.selector.isHidden()
    assert panel.selector.count() == 2
    panel.selector.setCurrentIndex(1)
    assert panel.title.text() == "other-vi.mp4"
    assert panel.current_receipt()["video_path"] == str(renamed)


def test_details_formatter_text_is_shown(tmp_path):
    panel = ResultPanel(details_formatter=lambda receipt: f"mode={receipt['subtitle_type']}")
    panel.load_receipt(_receipt(tmp_path))

    assert panel.details.text() == "mode=1"
    assert not panel.details.isHidden()


def test_space_key_toggles_playback(tmp_path, monkeypatch):
    panel, _ = _panel()
    panel.load_receipt(_receipt(tmp_path))
    calls = []
    monkeypatch.setattr(panel, "toggle_play", lambda: calls.append("toggle"))

    panel.keyPressEvent(QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Space, Qt.KeyboardModifier.NoModifier))

    assert calls == ["toggle"]


def test_result_dialog_releases_player_on_close(tmp_path):
    dialog = ResultDialog([_receipt(tmp_path)])
    assert not dialog.panel.player.source().isEmpty()

    dialog.close()

    assert dialog.panel.player.source().isEmpty()


def test_completion_opens_one_result_dialog(tmp_path, monkeypatch):
    from videotrans.mainwin._actions_task import WinActionTaskMixin
    from videotrans.ui import result_history

    history = tmp_path / "history.json"
    monkeypatch.setattr(result_history, "default_history_path", lambda: history)

    parent = QWidget()
    action = SimpleNamespace(main=parent, result_dialog=None)
    first = WinActionTaskMixin.show_result_dialog(action, [_receipt(tmp_path)])
    action.result_dialog = first

    assert first.isVisible()
    assert first.panel.title.text() == "clip-vi.mp4"
    assert first.panel.details.text()

    second = WinActionTaskMixin.show_result_dialog(action, [first.panel.current_receipt()])
    app.processEvents()

    assert second.isVisible()
    assert result_history.load_history(history)[0]["video_path"] == first.panel.current_receipt()["video_path"]
    second.close()


def _full_receipt(tmp_path, subtitle_type=2):
    receipt = _receipt(tmp_path)
    out = Path(receipt["target_dir"])
    source = tmp_path / "source.mp4"
    source.write_bytes(b"\0" * 64)
    en = out / "en.srt"
    en.write_text("1\n00:00:00,000 --> 00:00:01,000\nHello\n", encoding="utf-8")
    receipt.update(
        subtitle_type=subtitle_type,
        source_video=str(source),
        source_sub=str(en),
        target_sub=receipt["subtitle_paths"][0],
        output_srt=2,
        video_autorate=False,
    )
    return receipt


def test_mode_buttons_require_original_video(tmp_path):
    panel, _ = _panel()
    panel.load_receipt(_receipt(tmp_path))

    assert panel.mode_buttons["translated"].isEnabled()
    assert not panel.mode_buttons["original"].isEnabled()
    assert not panel.mode_buttons["side"].isEnabled()
    panel.set_mode("original")
    assert panel.mode() == "translated"


def test_switching_modes_changes_sources_and_compare_view(tmp_path):
    receipt = _full_receipt(tmp_path)
    panel, _ = _panel()
    panel.load_receipt(receipt)

    panel.set_mode("original")
    assert panel.mode() == "original"
    assert Path(panel.player.source().toLocalFile()) == Path(receipt["source_video"])
    assert panel.caption.isHidden()

    panel.set_mode("side")
    assert Path(panel.player.source().toLocalFile()) == Path(receipt["video_path"])
    assert Path(panel.compare_player.source().toLocalFile()) == Path(receipt["source_video"])
    assert not panel.compare_widget.isHidden()

    panel.set_mode("translated")
    assert panel.compare_widget.isHidden()
    assert panel.compare_player.source().isEmpty()


def test_mode_switch_ignores_stale_loaded_status_before_new_source_loads(tmp_path, monkeypatch):
    from PySide6.QtMultimedia import QMediaPlayer

    panel, _ = _panel()
    panel.load_receipt(_full_receipt(tmp_path))
    positions, plays = [], []
    monkeypatch.setattr(panel.player, "setPosition", positions.append)
    monkeypatch.setattr(panel.player, "play", lambda: plays.append(True))
    panel._pending_position = 975
    panel._resume_after_load = True
    panel._new_source_loading = False
    status = QMediaPlayer.MediaStatus

    panel._on_media_status(status.LoadedMedia)
    assert positions == [] and plays == []

    panel._on_media_status(status.LoadingMedia)
    panel._on_media_status(status.LoadedMedia)
    assert positions == [975] and plays == [True]
    assert panel._pending_position is None


def test_caption_strip_follows_soft_subtitle_cues(tmp_path):
    from videotrans.ui.result_panel import caption_at, caption_cues

    receipt = _full_receipt(tmp_path, subtitle_type=4)
    tracks = caption_cues(receipt)

    assert caption_at(tracks, 500) == "Xin chào\nHello"
    assert caption_at(tracks, 1500) == ""
    assert caption_at(caption_cues(dict(receipt, output_srt=1)), 500) == "Hello\nXin chào"
    assert caption_cues(dict(receipt, subtitle_type=1)) == []

    panel, _ = _panel()
    panel.load_receipt(receipt)
    panel._on_position_changed(500)
    assert panel.caption.text() == "Xin chào\nHello"
    assert not panel.caption.isHidden()


def test_selector_lists_current_then_recent_without_duplicates(tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    current = _receipt(tmp_path / "a")
    older = _receipt(tmp_path / "b")
    panel, _ = _panel()

    panel.load_receipts([current], recent=[current, older])

    assert panel.selector.count() == 2
    assert not panel.selector.isHidden()
    assert panel.selector.itemText(1).startswith(tr("result_recent"))


def test_reexport_button_follows_support(tmp_path):
    panel, _ = _panel()
    panel.load_receipt(_full_receipt(tmp_path))
    assert panel.reexport_button.isEnabled()

    panel.load_receipt(dict(panel.current_receipt(), video_autorate=True))
    assert not panel.reexport_button.isEnabled()
    assert panel.reexport_button.toolTip() == tr("reexport_unsupported_autorate")


def test_edit_and_reexport_runs_worker_and_loads_new_file(tmp_path):
    receipt = _full_receipt(tmp_path)
    new_video = Path(receipt["video_path"]).with_name("clip-vi-2.mp4")
    new_video.write_bytes(b"\0" * 100)

    class AcceptingEditor:
        def __init__(self, srt_path, parent):
            self.srt_path = srt_path

        def exec(self):
            return True

    runs = []
    panel = ResultPanel(
        editor_factory=AcceptingEditor,
        reexport_runner=lambda r: runs.append(r) or dict(r, video_path=str(new_video)),
    )
    emitted = []
    panel.reexported.connect(emitted.append)
    panel.load_receipt(receipt)

    panel.edit_and_reexport()
    assert panel.wait_for_reexport(10000)
    app.processEvents()

    assert runs and runs[0]["video_path"] == receipt["video_path"]
    assert panel.title.text() == "clip-vi-2.mp4"
    assert panel.selector.count() == 2
    assert emitted and emitted[0]["video_path"] == str(new_video)
    assert panel.reexport_status.text() == tr("result_reexport_done")


def test_cancelled_edit_does_not_reexport(tmp_path):
    class CancelledEditor:
        def __init__(self, *args):
            pass

        def exec(self):
            return False

    runs = []
    panel = ResultPanel(editor_factory=CancelledEditor, reexport_runner=runs.append)
    panel.load_receipt(_full_receipt(tmp_path))
    panel.edit_and_reexport()

    assert runs == []


def test_reexport_failure_is_reported(tmp_path):
    def failing(_receipt):
        raise RuntimeError("encoder exploded")

    panel = ResultPanel(reexport_runner=failing)
    panel.load_receipt(_full_receipt(tmp_path))
    panel.start_reexport(panel.current_receipt())
    assert panel.wait_for_reexport(10000)
    app.processEvents()

    assert tr("result_reexport_failed") in panel.reexport_status.text()
    assert "encoder exploded" in panel.reexport_status.text()
    assert panel.reexport_button.isEnabled()


def test_subtitle_editor_saves_text_and_keeps_timings(tmp_path):
    from videotrans.ui.result_subtitle_editor import ResultSubtitleEditor

    srt = tmp_path / "vi.srt"
    srt.write_text("1\n00:00:00,500 --> 00:00:01,500\nXin chào\n\n2\n00:00:02,000 --> 00:00:03,000\nTạm biệt\n", encoding="utf-8")
    editor = ResultSubtitleEditor(str(srt))

    assert not (editor.table.item(0, 0).flags() & Qt.ItemFlag.ItemIsEditable)
    assert editor.table.item(0, 1).flags() & Qt.ItemFlag.ItemIsEditable
    editor.table.item(1, 1).setText("Hẹn gặp lại")
    assert editor.has_unsaved_changes
    assert editor.status.text() == tr("result_edit_unsaved")

    editor.save_and_accept()

    text = srt.read_text(encoding="utf-8")
    assert "00:00:02,000 --> 00:00:03,000\nHẹn gặp lại" in text
    assert "Xin chào" in text
    assert not editor.has_unsaved_changes


def test_subtitle_editor_asks_before_discarding(tmp_path):
    from videotrans.ui.result_subtitle_editor import ResultSubtitleEditor

    srt = tmp_path / "vi.srt"
    srt.write_text("1\n00:00:00,500 --> 00:00:01,500\nXin chào\n", encoding="utf-8")
    answers = [False, True]
    editor = ResultSubtitleEditor(str(srt), confirm=lambda: answers.pop(0))
    editor.show()
    editor.table.item(0, 1).setText("Đã sửa")

    editor.reject()
    assert editor.isVisible()
    editor.reject()
    assert not editor.isVisible()
    assert "Xin chào" in srt.read_text(encoding="utf-8")
