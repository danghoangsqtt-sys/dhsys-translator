"""Wizard step 1: choose one or more videos, the output folder and a purpose."""

from pathlib import Path
from typing import Callable, Dict, List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from videotrans.configure._i18n import tr
from videotrans.ui.wizard.presets import PURPOSE_DUB_SUBTITLES, PURPOSE_SRT_ONLY, PURPOSE_SUBTITLES_ONLY

PURPOSE_LABELS = (
    (PURPOSE_DUB_SUBTITLES, "wizard_purpose_dub", "wizard_purpose_dub_hint"),
    (PURPOSE_SUBTITLES_ONLY, "wizard_purpose_subtitles", "wizard_purpose_subtitles_hint"),
    (PURPOSE_SRT_ONLY, "wizard_purpose_srt", "wizard_purpose_srt_hint"),
)

TILE_STYLE = """
QPushButton[wizardTile="true"] { text-align: left; padding: 10px 12px; border: 1px solid #d9e0dc;
    border-radius: 10px; background: #ffffff; color: #17211c; }
QPushButton[wizardTile="true"]:checked { border: 2px solid #14452f; background: #e7f0eb; }
QFrame#wizardDropZone { border: 2px dashed #d9e0dc; border-radius: 10px; background: #f4f6f5; }
QFrame#wizardDropZone[dragActive="true"] { border-color: #2f7956; background: #e7f0eb; }
"""


def allowed_extensions() -> List[str]:
    from videotrans.configure import constants

    return [ext.lower() for ext in constants.VIDEO_EXTS + constants.AUDIO_EXITS]


def default_probe(path: str) -> Dict:
    from videotrans.util.help_ffmpeg import get_video_info

    return get_video_info(path)


def describe_media(info: Dict) -> str:
    seconds = max(0, int(info.get("time", 0)) // 1000)
    hours, rest = divmod(seconds, 3600)
    minutes, secs = divmod(rest, 60)
    duration = f"{hours}:{minutes:02d}:{secs:02d}" if hours else f"{minutes}:{secs:02d}"
    width, height = int(info.get("width") or 0), int(info.get("height") or 0)
    parts = [duration]
    if width and height:
        parts.append(f"{width}×{height}")
    elif info.get("video_streams") == 0:
        parts.append(tr("wizard_audio_only"))
    return " · ".join(parts)


def tile(title: str, hint: str) -> QPushButton:
    button = QPushButton(f"{title}\n{hint}".replace("&", "&&"))
    button.setCheckable(True)
    button.setProperty("wizardTile", True)
    button.setMinimumHeight(64)
    return button


class DropZone(QFrame):
    files_dropped = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("wizardDropZone")
        self.setAcceptDrops(True)
        self.setMinimumHeight(150)

    def _set_active(self, active: bool):
        self.setProperty("dragActive", active)
        self.style().unpolish(self)
        self.style().polish(self)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            self._set_active(True)
            event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        self._set_active(False)

    def dropEvent(self, event):
        self._set_active(False)
        paths = [url.toLocalFile() for url in event.mimeData().urls() if url.isLocalFile()]
        if paths:
            self.files_dropped.emit(paths)
            event.acceptProposedAction()


class VideoStep(QWidget):
    """Collects input files and the job purpose; owns no processing logic."""

    changed = Signal()
    purpose_changed = Signal(str)

    def __init__(self, adapter, parent=None, *, probe: Optional[Callable[[str], Dict]] = None,
                 choose_files: Optional[Callable[[], List[str]]] = None,
                 choose_folder: Optional[Callable[[], str]] = None):
        super().__init__(parent)
        self.setObjectName("wizardVideoStep")
        self.setStyleSheet(TILE_STYLE)
        self.adapter = adapter
        self._probe = probe or default_probe
        self._choose_files = choose_files or self._dialog_files
        self._choose_folder = choose_folder or self._dialog_folder
        self._files: List[str] = []
        self._infos: Dict[str, Dict] = {}

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(18)

        left = QVBoxLayout()
        self.drop_zone = DropZone()
        self.drop_zone.files_dropped.connect(self.add_files)
        zone_layout = QVBoxLayout(self.drop_zone)
        zone_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title = QLabel(tr("wizard_drop_title"))
        title.setStyleSheet("font-size:16px;font-weight:600;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        zone_layout.addWidget(title)
        self.choose_button = QPushButton(tr("wizard_choose_videos"))
        self.choose_button.setObjectName("wizardChooseVideos")
        self.choose_button.clicked.connect(self._pick_files)
        zone_layout.addWidget(self.choose_button, 0, Qt.AlignmentFlag.AlignCenter)
        formats = QLabel(tr("wizard_drop_formats"))
        formats.setStyleSheet("color:#65716b;")
        formats.setAlignment(Qt.AlignmentFlag.AlignCenter)
        zone_layout.addWidget(formats)
        left.addWidget(self.drop_zone)

        self.file_list = QListWidget()
        self.file_list.setObjectName("wizardFileList")
        self.file_list.setMinimumHeight(110)
        left.addWidget(self.file_list, 1)

        self.message = QLabel()
        self.message.setObjectName("wizardVideoMessage")
        self.message.setWordWrap(True)
        self.message.setStyleSheet("color:#8a5a00;")
        self.message.hide()
        left.addWidget(self.message)

        output_row = QHBoxLayout()
        self.output_label = QLabel()
        self.output_label.setObjectName("wizardOutputDir")
        self.output_label.setWordWrap(True)
        self.output_label.setStyleSheet("color:#65716b;")
        output_row.addWidget(self.output_label, 1)
        self.output_button = QPushButton(tr("wizard_change_output"))
        self.output_button.setObjectName("wizardChangeOutput")
        self.output_button.clicked.connect(self._pick_folder)
        output_row.addWidget(self.output_button)
        left.addLayout(output_row)
        root.addLayout(left, 3)

        right = QVBoxLayout()
        purpose_title = QLabel(tr("wizard_purpose_title"))
        purpose_title.setStyleSheet("font-size:15px;font-weight:600;")
        right.addWidget(purpose_title)
        self.purpose_group = QButtonGroup(self)
        self.purpose_group.setExclusive(True)
        self.purpose_buttons = {}
        for key, title_key, hint_key in PURPOSE_LABELS:
            button = tile(tr(title_key), tr(hint_key))
            button.setObjectName(f"wizardPurpose_{key}")
            button.clicked.connect(lambda _checked=False, value=key: self.set_purpose(value))
            self.purpose_group.addButton(button)
            self.purpose_buttons[key] = button
            right.addWidget(button)
        note = QLabel(tr("wizard_purpose_note"))
        note.setWordWrap(True)
        note.setStyleSheet("color:#65716b;")
        right.addWidget(note)
        right.addStretch(1)
        root.addLayout(right, 2)

        self.purpose_buttons[adapter.current_purpose()].setChecked(True)
        self.set_files(adapter.videos())

    # ------------------------------------------------------------- files
    def files(self) -> List[str]:
        return list(self._files)

    def is_ready(self) -> bool:
        return any(Path(path).is_file() for path in self._files)

    def total_duration_ms(self) -> int:
        return sum(int(self._infos.get(path, {}).get("time", 0)) for path in self._files)

    def add_files(self, paths: List[str]):
        allowed = set(allowed_extensions())
        rejected = []
        merged = list(self._files)
        for raw in paths:
            path = Path(raw).as_posix()
            if Path(path).is_dir():
                merged += [p.as_posix() for p in sorted(Path(path).rglob("*"))
                           if p.is_file() and p.suffix[1:].lower() in allowed and p.as_posix() not in merged]
                continue
            if Path(path).suffix[1:].lower() not in allowed or not Path(path).is_file():
                rejected.append(Path(path).name)
            elif path not in merged:
                merged.append(path)
        self.set_files(merged)
        if rejected:
            self.message.setText(tr("wizard_rejected_files") + " " + ", ".join(rejected[:5]))
            self.message.show()

    def set_files(self, paths: List[str]):
        self._files = [Path(path).as_posix() for path in paths]
        self.message.hide()
        self.file_list.clear()
        for path in self._files:
            if path not in self._infos:
                try:
                    self._infos[path] = self._probe(path)
                except Exception:
                    self._infos[path] = {}
            info = self._infos[path]
            row = QWidget()
            layout = QHBoxLayout(row)
            layout.setContentsMargins(6, 4, 6, 4)
            name = QLabel(f"<b>{Path(path).name}</b><br><span style='color:#65716b'>"
                          f"{describe_media(info) if info else tr('wizard_unreadable')}</span>")
            name.setToolTip(path)
            layout.addWidget(name, 1)
            remove = QPushButton(tr("wizard_remove"))
            remove.setObjectName("wizardRemoveVideo")
            remove.clicked.connect(lambda _checked=False, value=path: self.remove_file(value))
            layout.addWidget(remove)
            item = QListWidgetItem()
            item.setSizeHint(row.sizeHint())
            item.setData(Qt.ItemDataRole.UserRole, path)
            self.file_list.addItem(item)
            self.file_list.setItemWidget(item, row)
        self.file_list.setVisible(bool(self._files))
        self.adapter.set_videos(self._files)
        self._update_output_label()
        self.changed.emit()

    def remove_file(self, path: str):
        self.set_files([item for item in self._files if item != path])

    def _pick_files(self):
        paths = self._choose_files()
        if paths:
            self.add_files(paths)

    def _dialog_files(self) -> List[str]:
        pattern = " ".join("*." + ext for ext in allowed_extensions())
        names, _ = QFileDialog.getOpenFileNames(self, tr("wizard_choose_videos"), "", f"Media ({pattern})")
        return names

    # ------------------------------------------------------------ output
    def _update_output_label(self):
        folder = self.adapter.output_dir()
        if not folder and self._files:
            folder = (Path(self._files[0]).parent / "_video_out").as_posix()
        self.output_label.setText(tr("wizard_output_dir") + " " + (folder or tr("wizard_output_default")))

    def _pick_folder(self):
        folder = self._choose_folder()
        if folder:
            self.adapter.set_output_dir(folder)
            self._update_output_label()

    def _dialog_folder(self) -> str:
        return QFileDialog.getExistingDirectory(self, tr("wizard_change_output"), "")

    # ----------------------------------------------------------- purpose
    def purpose(self) -> str:
        for key, button in self.purpose_buttons.items():
            if button.isChecked():
                return key
        return PURPOSE_DUB_SUBTITLES

    def set_purpose(self, purpose: str):
        self.purpose_buttons[purpose].setChecked(True)
        self.adapter.apply_purpose(purpose)
        self.purpose_changed.emit(purpose)
        self.changed.emit()
