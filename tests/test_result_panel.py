import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

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


def test_completion_opens_one_result_dialog(tmp_path):
    from videotrans.mainwin._actions_task import WinActionTaskMixin

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
    second.close()
