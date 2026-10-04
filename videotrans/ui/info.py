"""Offline product information dialog."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QDialog, QLabel, QPushButton, QVBoxLayout

from videotrans import VERSION
from videotrans.configure.config import ROOT_DIR, tr


class Ui_info(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon(f"{ROOT_DIR}/videotrans/styles/icon.ico"))
        self.setWindowTitle(tr("About"))
        self.resize(520, 300)
        self.setStyleSheet("""
            QDialog { background: #101820; }
            QLabel { color: #f4f7f4; }
            QPushButton { background: #6fe0c4; color: #102028; border: 0;
                          border-radius: 9px; padding: 9px 20px; font-weight: 700; }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 27, 30, 27)
        layout.setSpacing(14)
        title = QLabel(tr("Video Workshop"))
        title.setStyleSheet("font-size: 28px; font-weight: 700;")
        layout.addWidget(title)
        version = QLabel(f"{tr('Version')} {VERSION}")
        version.setStyleSheet("color: #6fe0c4;")
        layout.addWidget(version)
        description = QLabel(tr("Create subtitles, translate video and add new voices in one desktop workspace."))
        description.setWordWrap(True)
        layout.addWidget(description)
        license_note = QLabel(tr("Distributed under GNU GPL v3. See the LICENSE file included with the application."))
        license_note.setWordWrap(True)
        license_note.setStyleSheet("color: #b7cbcb;")
        layout.addWidget(license_note)
        layout.addStretch()
        close = QPushButton(tr("Close"))
        close.clicked.connect(self.close)
        layout.addWidget(close, alignment=Qt.AlignmentFlag.AlignRight)
