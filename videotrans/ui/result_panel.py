"""Result review surface shown after a translated-video job finishes.

The panel is driven only by the serializable ``output_receipt`` payload built in
``videotrans/task/subtitle_output.py``; it never reads task internals or runs
FFmpeg.  Playback uses Qt Multimedia, which the Windows package already bundles.
"""

from pathlib import Path
from typing import Callable, Iterable, List, Optional

from PySide6.QtCore import QUrl, Qt, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSlider,
    QStyle,
    QVBoxLayout,
    QWidget,
)

from videotrans.configure._i18n import tr

SEEK_STEP_MS = 5000


def format_duration(ms: int) -> str:
    """Format milliseconds as m:ss or h:mm:ss for the time label."""
    seconds = max(0, int(ms) // 1000)
    hours, rest = divmod(seconds, 3600)
    minutes, seconds = divmod(rest, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"


def format_size(num_bytes: int) -> str:
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} GB"


def receipt_files(receipt: dict) -> List[Path]:
    """Ordered, de-duplicated output files named by a receipt (missing ones included)."""
    ordered = []
    for raw in [receipt.get("video_path")] + list(receipt.get("subtitle_paths") or []) + list(receipt.get("audio_paths") or []):
        if raw and Path(raw) not in ordered:
            ordered.append(Path(raw))
    return ordered


def receipt_folder(receipt: dict) -> Optional[Path]:
    if receipt.get("target_dir"):
        return Path(receipt["target_dir"])
    video = receipt.get("video_path")
    return Path(video).parent if video else None


class ResultPanel(QWidget):
    """Plays the finished video and exposes the output files and follow-up actions."""

    translate_another = Signal()

    def __init__(self, parent=None, *, details_formatter: Optional[Callable[[dict], str]] = None,
                 open_url: Optional[Callable[[QUrl], bool]] = None):
        super().__init__(parent)
        self.setObjectName("resultPanel")
        self._receipts: List[dict] = []
        self._receipt: dict = {}
        self._details_formatter = details_formatter
        self._open_url = open_url or QDesktopServices.openUrl
        self._seeking = False

        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(0.8)

        self._build_ui()
        self.player.setVideoOutput(self.video_widget)
        self.player.durationChanged.connect(self._on_duration_changed)
        self.player.positionChanged.connect(self._on_position_changed)
        self.player.playbackStateChanged.connect(self._sync_play_button)
        self.player.errorOccurred.connect(self._on_player_error)

    # ------------------------------------------------------------------ UI
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        header = QHBoxLayout()
        self.title = QLabel()
        self.title.setObjectName("resultTitle")
        self.title.setStyleSheet("font-size:16px;font-weight:600;")
        self.title.setWordWrap(True)
        header.addWidget(self.title, 1)
        self.selector = QComboBox()
        self.selector.setObjectName("resultSelector")
        self.selector.setToolTip(tr("result_select_video"))
        self.selector.currentIndexChanged.connect(self._on_selector_changed)
        self.selector.hide()
        header.addWidget(self.selector)
        root.addLayout(header)

        self.video_widget = QVideoWidget()
        self.video_widget.setObjectName("resultVideo")
        self.video_widget.setMinimumSize(320, 180)
        self.video_widget.setStyleSheet("background:#111;")
        root.addWidget(self.video_widget, 1)

        self.message = QLabel()
        self.message.setObjectName("resultMessage")
        self.message.setWordWrap(True)
        self.message.hide()
        root.addWidget(self.message)

        controls = QHBoxLayout()
        self.play_button = QPushButton()
        self.play_button.setObjectName("resultPlay")
        self.play_button.clicked.connect(self.toggle_play)
        controls.addWidget(self.play_button)
        self.position = QSlider(Qt.Orientation.Horizontal)
        self.position.setObjectName("resultPosition")
        self.position.setRange(0, 0)
        self.position.sliderPressed.connect(lambda: setattr(self, "_seeking", True))
        self.position.sliderReleased.connect(self._on_slider_released)
        controls.addWidget(self.position, 1)
        self.time_label = QLabel("0:00 / 0:00")
        self.time_label.setObjectName("resultTime")
        controls.addWidget(self.time_label)
        self.volume = QSlider(Qt.Orientation.Horizontal)
        self.volume.setObjectName("resultVolume")
        self.volume.setRange(0, 100)
        self.volume.setValue(80)
        self.volume.setMaximumWidth(90)
        self.volume.setToolTip(tr("result_volume"))
        self.volume.valueChanged.connect(lambda value: self.audio_output.setVolume(value / 100))
        controls.addWidget(self.volume)
        self.fullscreen_button = QPushButton(tr("result_fullscreen"))
        self.fullscreen_button.setObjectName("resultFullscreen")
        self.fullscreen_button.clicked.connect(lambda: self.video_widget.setFullScreen(True))
        controls.addWidget(self.fullscreen_button)
        root.addLayout(controls)

        files_label = QLabel(tr("result_output_files"))
        files_label.setStyleSheet("font-weight:600;")
        root.addWidget(files_label)
        self.files = QListWidget()
        self.files.setObjectName("resultFiles")
        self.files.setMaximumHeight(120)
        self.files.itemDoubleClicked.connect(self._open_file_item)
        root.addWidget(self.files)

        self.details = QLabel()
        self.details.setObjectName("resultDetails")
        self.details.setWordWrap(True)
        self.details.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.details.setStyleSheet("color:#65716b;")
        root.addWidget(self.details)

        actions = QHBoxLayout()
        self.open_folder_button = QPushButton(tr("result_open_folder"))
        self.open_folder_button.setObjectName("resultOpenFolder")
        self.open_folder_button.clicked.connect(self.open_folder)
        actions.addWidget(self.open_folder_button)
        self.open_external_button = QPushButton(tr("result_open_external"))
        self.open_external_button.setObjectName("resultOpenExternal")
        self.open_external_button.clicked.connect(self.open_external)
        actions.addWidget(self.open_external_button)
        actions.addStretch(1)
        self.translate_another_button = QPushButton(tr("result_translate_another"))
        self.translate_another_button.setObjectName("resultTranslateAnother")
        self.translate_another_button.clicked.connect(self._request_translate_another)
        actions.addWidget(self.translate_another_button)
        root.addLayout(actions)

        self._sync_play_button()

    # -------------------------------------------------------------- loading
    def load_receipt(self, receipt: dict):
        self.load_receipts([receipt])

    def load_receipts(self, receipts: Iterable[dict]):
        self._receipts = [dict(item) for item in receipts if isinstance(item, dict)]
        self.selector.blockSignals(True)
        self.selector.clear()
        for receipt in self._receipts:
            self.selector.addItem(Path(receipt.get("video_path") or "?").name)
        self.selector.setVisible(len(self._receipts) > 1)
        self.selector.blockSignals(False)
        self._show_receipt(self._receipts[0] if self._receipts else {})

    def _on_selector_changed(self, index):
        if 0 <= index < len(self._receipts):
            self._show_receipt(self._receipts[index])

    def _show_receipt(self, receipt: dict):
        self.release_media()
        self._receipt = receipt
        video = Path(receipt["video_path"]) if receipt.get("video_path") else None
        self.title.setText(video.name if video else tr("result_no_output"))

        self.files.clear()
        for path in receipt_files(receipt):
            exists = path.is_file()
            label = f"{path.name}  ·  {format_size(path.stat().st_size)}" if exists else f"{path.name}  ·  {tr('result_file_missing')}"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, str(path))
            item.setToolTip(str(path))
            if not exists:
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
            self.files.addItem(item)

        details = self._details_formatter(receipt) if (self._details_formatter and receipt) else ""
        self.details.setText(details)
        self.details.setVisible(bool(details))

        playable = bool(video and video.is_file())
        for widget in (self.play_button, self.position, self.fullscreen_button, self.open_external_button):
            widget.setEnabled(playable)
        folder = receipt_folder(receipt)
        self.open_folder_button.setEnabled(bool(folder and folder.is_dir()))
        if playable:
            self.message.hide()
            self.player.setSource(QUrl.fromLocalFile(str(video)))
        else:
            self.message.setText(tr("result_video_missing") + (f"\n{video}" if video else ""))
            self.message.show()

    def current_receipt(self) -> dict:
        return dict(self._receipt)

    # ------------------------------------------------------------- playback
    def toggle_play(self):
        if not self.play_button.isEnabled():
            return
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def seek_relative(self, delta_ms: int):
        target = max(0, self.player.position() + delta_ms)
        duration = self.player.duration()
        if duration > 0:
            target = min(target, duration)
        self.player.setPosition(target)

    def release_media(self):
        """Stop playback and drop the source so Windows releases the output file."""
        self.player.stop()
        self.player.setSource(QUrl())
        self.position.setRange(0, 0)
        self.time_label.setText("0:00 / 0:00")

    def _sync_play_button(self, *_):
        playing = self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState
        icon = QStyle.StandardPixmap.SP_MediaPause if playing else QStyle.StandardPixmap.SP_MediaPlay
        self.play_button.setIcon(self.style().standardIcon(icon))
        self.play_button.setToolTip(tr("result_pause") if playing else tr("result_play"))

    def _on_duration_changed(self, duration):
        self.position.setRange(0, max(0, duration))
        self._update_time_label(self.player.position(), duration)

    def _on_position_changed(self, position):
        if not self._seeking:
            self.position.setValue(position)
        self._update_time_label(position, self.player.duration())

    def _on_slider_released(self):
        self._seeking = False
        self.player.setPosition(self.position.value())

    def _update_time_label(self, position, duration):
        self.time_label.setText(f"{format_duration(position)} / {format_duration(duration)}")

    def _on_player_error(self, *_):
        if self.player.error() != QMediaPlayer.Error.NoError:
            self.message.setText(tr("result_playback_error") + f"\n{self.player.errorString()}")
            self.message.show()

    # -------------------------------------------------------------- actions
    def open_folder(self):
        folder = receipt_folder(self._receipt)
        if folder and folder.is_dir():
            self._open_url(QUrl.fromLocalFile(str(folder)))

    def open_external(self):
        video = self._receipt.get("video_path")
        if video and Path(video).is_file():
            self.player.pause()
            self._open_url(QUrl.fromLocalFile(str(video)))

    def _open_file_item(self, item: QListWidgetItem):
        path = item.data(Qt.ItemDataRole.UserRole)
        if path and Path(path).is_file():
            self._open_url(QUrl.fromLocalFile(path))

    def _request_translate_another(self):
        self.release_media()
        self.translate_another.emit()

    # ------------------------------------------------------------ lifecycle
    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key.Key_Space:
            self.toggle_play()
        elif key == Qt.Key.Key_Left:
            self.seek_relative(-SEEK_STEP_MS)
        elif key == Qt.Key.Key_Right:
            self.seek_relative(SEEK_STEP_MS)
        else:
            super().keyPressEvent(event)
            return
        event.accept()

    def hideEvent(self, event):
        self.player.pause()
        super().hideEvent(event)

    def closeEvent(self, event):
        self.release_media()
        super().closeEvent(event)


class ResultDialog(QDialog):
    """Non-modal window that hosts a ResultPanel for the classic workspace."""

    def __init__(self, receipts: Iterable[dict], parent=None, *,
                 details_formatter: Optional[Callable[[dict], str]] = None):
        super().__init__(parent)
        self.setObjectName("resultDialog")
        self.setWindowTitle(tr("output_receipt_title"))
        self.resize(900, 680)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.panel = ResultPanel(self, details_formatter=details_formatter)
        self.panel.translate_another.connect(self.close)
        layout.addWidget(self.panel)
        self.panel.load_receipts(receipts)
        self.panel.setFocus()

    def closeEvent(self, event):
        self.panel.release_media()
        super().closeEvent(event)

    def done(self, result):
        self.panel.release_media()
        super().done(result)
