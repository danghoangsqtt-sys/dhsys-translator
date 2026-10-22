"""Result review surface shown after a translated-video job finishes.

The panel is driven only by the serializable ``output_receipt`` payload built in
``videotrans/task/subtitle_output.py``; it never reads task internals.  Playback
uses Qt Multimedia, which the Windows package already bundles.  Re-export runs
the separate ``videotrans/task/reexport.py`` helper on a worker thread.
"""

from pathlib import Path
from typing import Callable, Iterable, List, Optional, Tuple

from PySide6.QtCore import QThread, QUrl, Qt, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import (
    QButtonGroup,
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
SYNC_TOLERANCE_MS = 300
SOFT_SUBTITLE_TYPES = (2, 4)

MODE_TRANSLATED = "translated"
MODE_ORIGINAL = "original"
MODE_SIDE = "side"


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


def source_video(receipt: dict) -> Optional[Path]:
    raw = receipt.get("source_video")
    return Path(raw) if raw and Path(raw).is_file() else None


def _read_cues(path) -> List[Tuple[int, int, str]]:
    from videotrans.util.help_srt import get_subtitle_from_srt

    if not path or not Path(path).is_file():
        return []
    try:
        return [(item.start_time, item.end_time, item.text.strip())
                for item in get_subtitle_from_srt(str(path), is_file=True)]
    except Exception:
        return []


def caption_cues(receipt: dict) -> List[List[Tuple[int, int, str]]]:
    """Cue tracks to show under the video for soft-subtitle outputs, top line first."""
    if int(receipt.get("subtitle_type", 0)) not in SOFT_SUBTITLE_TYPES:
        return []
    target = _read_cues(receipt.get("target_sub"))
    if int(receipt.get("subtitle_type", 0)) != 4:
        return [target] if target else []
    source = _read_cues(receipt.get("source_sub"))
    tracks = [source, target] if int(receipt.get("output_srt", 2)) == 1 else [target, source]
    return [track for track in tracks if track]


def caption_at(tracks: List[List[Tuple[int, int, str]]], position_ms: int) -> str:
    lines = []
    for track in tracks:
        for start, end, text in track:
            if start <= position_ms < end:
                lines.append(text)
                break
    return "\n".join(lines)


def merge_receipts(current: Iterable[dict], recent: Iterable[dict]) -> List[dict]:
    """Current receipts first, then recent history, de-duplicated by output video."""
    merged, seen = [], set()
    for receipt in list(current) + list(recent):
        if not isinstance(receipt, dict):
            continue
        key = receipt.get("video_path")
        if not key or key in seen:
            continue
        seen.add(key)
        merged.append(dict(receipt))
    return merged


class ReexportWorker(QThread):
    """Runs the FFmpeg re-export off the UI thread."""

    succeeded = Signal(dict)
    failed = Signal(str)

    def __init__(self, receipt: dict, runner: Callable[[dict], dict], parent=None):
        super().__init__(parent)
        self._receipt = dict(receipt)
        self._runner = runner

    def run(self):
        try:
            self.succeeded.emit(self._runner(self._receipt))
        except Exception as error:
            self.failed.emit(str(error))


class ResultPanel(QWidget):
    """Plays the finished video and exposes the output files and follow-up actions."""

    translate_another = Signal()
    reexported = Signal(dict)

    def __init__(self, parent=None, *, details_formatter: Optional[Callable[[dict], str]] = None,
                 open_url: Optional[Callable[[QUrl], bool]] = None,
                 editor_factory: Optional[Callable] = None,
                 reexport_runner: Optional[Callable[[dict], dict]] = None):
        super().__init__(parent)
        self.setObjectName("resultPanel")
        self._receipts: List[dict] = []
        self._current_count = 0
        self._receipt: dict = {}
        self._details_formatter = details_formatter
        self._open_url = open_url or QDesktopServices.openUrl
        self._editor_factory = editor_factory
        self._reexport_runner = reexport_runner
        self._worker: Optional[ReexportWorker] = None
        self._seeking = False
        self._mode = MODE_TRANSLATED
        self._pending_position: Optional[int] = None
        self._resume_after_load = False
        self._new_source_loading = False
        self._caption_tracks: List[List[Tuple[int, int, str]]] = []

        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(0.8)
        # The original video in side-by-side mode is silent and follows the main player.
        self.compare_player = QMediaPlayer(self)

        self._build_ui()
        self.player.setVideoOutput(self.video_widget)
        self.compare_player.setVideoOutput(self.compare_widget)
        self.player.durationChanged.connect(self._on_duration_changed)
        self.player.positionChanged.connect(self._on_position_changed)
        self.player.playbackStateChanged.connect(self._sync_play_button)
        self.player.playbackStateChanged.connect(self._sync_compare_state)
        self.player.mediaStatusChanged.connect(self._on_media_status)
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

        modes = QHBoxLayout()
        self.mode_group = QButtonGroup(self)
        self.mode_group.setExclusive(True)
        self.mode_buttons = {}
        for mode, key in ((MODE_TRANSLATED, "result_mode_translated"),
                          (MODE_ORIGINAL, "result_mode_original"),
                          (MODE_SIDE, "result_mode_side")):
            button = QPushButton(tr(key))
            button.setObjectName(f"resultMode_{mode}")
            button.setCheckable(True)
            button.clicked.connect(lambda _checked=False, value=mode: self.set_mode(value))
            self.mode_group.addButton(button)
            self.mode_buttons[mode] = button
            modes.addWidget(button)
        modes.addStretch(1)
        self.mode_buttons[MODE_TRANSLATED].setChecked(True)
        root.addLayout(modes)

        videos = QHBoxLayout()
        self.video_widget = QVideoWidget()
        self.video_widget.setObjectName("resultVideo")
        self.video_widget.setMinimumSize(320, 180)
        self.video_widget.setStyleSheet("background:#111;")
        videos.addWidget(self.video_widget, 1)
        self.compare_widget = QVideoWidget()
        self.compare_widget.setObjectName("resultCompareVideo")
        self.compare_widget.setMinimumSize(320, 180)
        self.compare_widget.setStyleSheet("background:#111;")
        self.compare_widget.hide()
        videos.addWidget(self.compare_widget, 1)
        root.addLayout(videos, 1)

        self.caption = QLabel()
        self.caption.setObjectName("resultCaption")
        self.caption.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.caption.setWordWrap(True)
        self.caption.setMinimumHeight(40)
        self.caption.setStyleSheet("background:#17211c;color:#fff;font-size:15px;padding:6px;border-radius:6px;")
        self.caption.hide()
        root.addWidget(self.caption)

        self.message = QLabel()
        self.message.setObjectName("resultMessage")
        self.message.setWordWrap(True)
        self.message.hide()
        root.addWidget(self.message)

        # Re-export progress has its own line so asynchronous playback errors cannot hide it.
        self.reexport_status = QLabel()
        self.reexport_status.setObjectName("resultReexportStatus")
        self.reexport_status.setWordWrap(True)
        self.reexport_status.hide()
        root.addWidget(self.reexport_status)

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
        self.reexport_button = QPushButton(tr("result_edit_reexport").replace("&", "&&"))
        self.reexport_button.setObjectName("resultReexport")
        self.reexport_button.clicked.connect(self.edit_and_reexport)
        actions.addWidget(self.reexport_button)
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

    def load_receipts(self, receipts: Iterable[dict], recent: Iterable[dict] = ()):
        """Show current receipts first; recent history follows in the same selector."""
        current = [dict(item) for item in receipts if isinstance(item, dict)]
        self._current_count = len(current)
        self._receipts = merge_receipts(current, recent)
        self._rebuild_selector()
        self._show_receipt(self._receipts[0] if self._receipts else {})

    def _rebuild_selector(self, index: int = 0):
        self.selector.blockSignals(True)
        self.selector.clear()
        for position, receipt in enumerate(self._receipts):
            name = Path(receipt.get("video_path") or "?").name
            if position >= self._current_count:
                name = f"{tr('result_recent')} · {name}"
            self.selector.addItem(name)
        self.selector.setCurrentIndex(index if self._receipts else -1)
        self.selector.setVisible(len(self._receipts) > 1)
        self.selector.blockSignals(False)

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
        has_source = playable and source_video(receipt) is not None
        for mode in (MODE_ORIGINAL, MODE_SIDE):
            self.mode_buttons[mode].setEnabled(has_source)
        self.mode_buttons[MODE_TRANSLATED].setEnabled(playable)
        self._caption_tracks = caption_cues(receipt)
        self._update_reexport_button()

        self._mode = MODE_TRANSLATED
        self.mode_buttons[MODE_TRANSLATED].setChecked(True)
        self.compare_widget.hide()
        self._update_caption(0)
        if playable:
            self.message.hide()
            self.player.setSource(QUrl.fromLocalFile(str(video)))
        else:
            self.message.setText(tr("result_video_missing") + (f"\n{video}" if video else ""))
            self.message.show()

    def current_receipt(self) -> dict:
        return dict(self._receipt)

    def mode(self) -> str:
        return self._mode

    # ---------------------------------------------------------- compare modes
    def set_mode(self, mode: str):
        if mode not in self.mode_buttons or not self.mode_buttons[mode].isEnabled():
            self.mode_buttons[self._mode].setChecked(True)
            return
        video = self._receipt.get("video_path")
        original = source_video(self._receipt)
        if not video or (mode != MODE_TRANSLATED and original is None):
            return
        position = self.player.position()
        was_playing = self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState
        wanted = str(original) if mode == MODE_ORIGINAL else str(video)
        self._mode = mode
        self.mode_buttons[mode].setChecked(True)

        if Path(self.player.source().toLocalFile() or ".") != Path(wanted):
            self._pending_position = position
            self._resume_after_load = was_playing
            self._new_source_loading = False
            self.player.setSource(QUrl.fromLocalFile(wanted))

        if mode == MODE_SIDE:
            self.compare_player.setSource(QUrl.fromLocalFile(str(original)))
            self.compare_player.setPosition(position)
            self.compare_widget.show()
            if was_playing:
                self.compare_player.play()
        else:
            self.compare_player.stop()
            self.compare_player.setSource(QUrl())
            self.compare_widget.hide()
        self._update_caption(position)

    def _on_media_status(self, status):
        # setSource() can replay a stale LoadedMedia for the previous file before the
        # new one starts loading, so wait for LoadingMedia before restoring position.
        if self._pending_position is None:
            return
        if status == QMediaPlayer.MediaStatus.LoadingMedia:
            self._new_source_loading = True
            return
        loaded = (QMediaPlayer.MediaStatus.LoadedMedia, QMediaPlayer.MediaStatus.BufferedMedia)
        if status in loaded and self._new_source_loading:
            self._new_source_loading = False
            self.player.setPosition(self._pending_position)
            self._pending_position = None
            if self._resume_after_load:
                self._resume_after_load = False
                self.player.play()

    def _sync_compare_state(self, state):
        if self._mode != MODE_SIDE:
            return
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.compare_player.setPosition(self.player.position())
            self.compare_player.play()
        elif state == QMediaPlayer.PlaybackState.PausedState:
            self.compare_player.pause()
        else:
            self.compare_player.stop()

    def _sync_compare_position(self, position):
        if self._mode == MODE_SIDE and abs(self.compare_player.position() - position) > SYNC_TOLERANCE_MS:
            self.compare_player.setPosition(position)

    def _update_caption(self, position):
        if self._mode == MODE_ORIGINAL or not self._caption_tracks:
            self.caption.hide()
            return
        self.caption.setText(caption_at(self._caption_tracks, position))
        self.caption.show()

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
        """Stop playback and drop the sources so Windows releases the output files."""
        for player in (self.player, self.compare_player):
            player.stop()
            player.setSource(QUrl())
        self._pending_position = None
        self._resume_after_load = False
        self._new_source_loading = False
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
        self._sync_compare_position(position)
        self._update_caption(position)

    def _on_slider_released(self):
        self._seeking = False
        self.player.setPosition(self.position.value())

    def _update_time_label(self, position, duration):
        self.time_label.setText(f"{format_duration(position)} / {format_duration(duration)}")

    def _on_player_error(self, *_):
        if self.player.error() != QMediaPlayer.Error.NoError:
            self.message.setText(tr("result_playback_error") + f"\n{self.player.errorString()}")
            self.message.show()

    # ------------------------------------------------------------ re-export
    def _update_reexport_button(self):
        from videotrans.task.reexport import reexport_support

        supported, reason = reexport_support(self._receipt) if self._receipt else (False, "")
        busy = self._worker is not None and self._worker.isRunning()
        self.reexport_button.setEnabled(supported and not busy)
        self.reexport_button.setToolTip(tr(reason) if reason else tr("result_edit_reexport"))

    def edit_and_reexport(self):
        """Edit the target subtitles, then rebuild the video into a new file."""
        from videotrans.task.reexport import reexport_support

        supported, _ = reexport_support(self._receipt)
        if not supported or (self._worker is not None and self._worker.isRunning()):
            return
        factory = self._editor_factory
        if factory is None:
            from videotrans.ui.result_subtitle_editor import ResultSubtitleEditor
            factory = ResultSubtitleEditor
        editor = factory(self._receipt["target_sub"], self)
        if not editor.exec():
            return
        self.start_reexport(self._receipt)

    def start_reexport(self, receipt: dict):
        runner = self._reexport_runner
        if runner is None:
            from videotrans.task.reexport import run_reexport
            runner = run_reexport
        self.player.pause()
        self._worker = ReexportWorker(receipt, runner, self)
        self._worker.succeeded.connect(self._on_reexport_succeeded)
        self._worker.failed.connect(self._on_reexport_failed)
        self._worker.finished.connect(self._update_reexport_button)
        self.reexport_status.setText(tr("result_reexporting"))
        self.reexport_status.show()
        self._update_reexport_button()
        self._worker.start()
        return self._worker

    def _on_reexport_succeeded(self, receipt: dict):
        self._current_count += 1
        self._receipts = merge_receipts([receipt], self._receipts)
        self._rebuild_selector(0)
        self._show_receipt(self._receipts[0])
        self.reexport_status.setText(tr("result_reexport_done"))
        self.reexport_status.show()
        self.reexported.emit(dict(receipt))

    def _on_reexport_failed(self, error: str):
        self.reexport_status.setText(tr("result_reexport_failed") + f"\n{tr(error)}")
        self.reexport_status.show()

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
        self.compare_player.pause()
        super().hideEvent(event)

    def closeEvent(self, event):
        self.release_media()
        super().closeEvent(event)

    def wait_for_reexport(self, timeout_ms: int = 0) -> bool:
        if self._worker is None:
            return True
        return self._worker.wait(timeout_ms) if timeout_ms else self._worker.wait()


class ResultDialog(QDialog):
    """Non-modal window that hosts a ResultPanel for the classic workspace."""

    def __init__(self, receipts: Iterable[dict], parent=None, *,
                 details_formatter: Optional[Callable[[dict], str]] = None,
                 recent: Iterable[dict] = (),
                 record_history: Optional[Callable[[List[dict]], object]] = None):
        super().__init__(parent)
        self.setObjectName("resultDialog")
        self.setWindowTitle(tr("output_receipt_title"))
        self.resize(900, 720)
        self._record_history = record_history
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.panel = ResultPanel(self, details_formatter=details_formatter)
        self.panel.translate_another.connect(self.close)
        self.panel.reexported.connect(self._remember)
        layout.addWidget(self.panel)
        self.panel.load_receipts(receipts, recent)
        self.panel.setFocus()

    def _remember(self, receipt: dict):
        if self._record_history is None:
            return
        try:
            self._record_history([receipt])
        except Exception:
            pass

    def closeEvent(self, event):
        self.panel.release_media()
        super().closeEvent(event)

    def done(self, result):
        self.panel.release_media()
        super().done(result)
