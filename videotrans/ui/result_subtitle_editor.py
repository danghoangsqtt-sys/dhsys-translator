"""Text-only subtitle editor for a finished result.

Timings stay fixed so the edited subtitles remain aligned with the dubbed audio
that re-export reuses.  Behaviour follows Task 4.13: cells are focusable,
selectable and editable, unsaved edits are shown and confirmed, and nothing
closes on a timer.
"""

from pathlib import Path
from typing import List

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QHeaderView,
    QLabel,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from videotrans.configure._i18n import tr
from videotrans.util.help_srt import get_subtitle_from_srt


def write_srt(path: Path, cues: List[dict]):
    blocks = []
    for index, cue in enumerate(cues, start=1):
        text = cue["text"].strip() or " "
        blocks.append(f"{index}\n{cue['time']}\n{text}")
    Path(path).write_text("\n\n".join(blocks) + "\n", encoding="utf-8")


class ResultSubtitleEditor(QDialog):
    def __init__(self, srt_path: str, parent=None, *, confirm=None):
        super().__init__(parent)
        self.setObjectName("resultSubtitleEditor")
        self.setWindowTitle(tr("result_edit_subtitles"))
        self.resize(760, 560)
        self.srt_path = Path(srt_path)
        self._confirm = confirm or self._ask_discard
        self.cues = [
            {"time": item.time, "text": item.text}
            for item in get_subtitle_from_srt(str(self.srt_path), is_file=True)
        ]
        self.has_unsaved_changes = False

        layout = QVBoxLayout(self)
        hint = QLabel(tr("result_edit_hint"))
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self.table = QTableWidget(len(self.cues), 2)
        self.table.setObjectName("resultSubtitleTable")
        self.table.setHorizontalHeaderLabels([tr("result_edit_time"), tr("result_edit_text")])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked
            | QAbstractItemView.EditTrigger.EditKeyPressed
            | QAbstractItemView.EditTrigger.AnyKeyPressed
        )
        for row, cue in enumerate(self.cues):
            time_item = QTableWidgetItem(cue["time"])
            time_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self.table.setItem(row, 0, time_item)
            self.table.setItem(row, 1, QTableWidgetItem(cue["text"]))
        self.table.itemChanged.connect(self._mark_changed)
        layout.addWidget(self.table, 1)

        self.status = QLabel()
        self.status.setObjectName("resultSubtitleStatus")
        layout.addWidget(self.status)

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.button(QDialogButtonBox.StandardButton.Save).setText(tr("result_save_and_reexport").replace("&", "&&"))
        self.buttons.accepted.connect(self.save_and_accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)
        self._update_status()

    def _mark_changed(self, item):
        if item.column() == 1:
            self.has_unsaved_changes = True
            self._update_status()

    def _update_status(self):
        self.status.setText(tr("result_edit_unsaved") if self.has_unsaved_changes else "")

    def edited_cues(self) -> List[dict]:
        return [
            {"time": cue["time"], "text": self.table.item(row, 1).text()}
            for row, cue in enumerate(self.cues)
        ]

    def save_and_accept(self):
        write_srt(self.srt_path, self.edited_cues())
        self.has_unsaved_changes = False
        self._update_status()
        self.accept()

    def _ask_discard(self) -> bool:
        reply = QMessageBox.question(
            self,
            tr("result_edit_subtitles"),
            tr("result_edit_discard"),
            QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        return reply == QMessageBox.StandardButton.Discard

    def reject(self):
        if self.has_unsaved_changes and not self._confirm():
            return
        super().reject()
