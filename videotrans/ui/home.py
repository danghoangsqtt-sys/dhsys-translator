"""A desktop start page that routes to the existing editing and utility windows."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QVBoxLayout, QWidget,
)

from videotrans.configure.config import tr


class HomePage(QWidget):
    workspace_requested = Signal()
    tool_requested = Signal(str)
    locale_requested = Signal(str)

    def __init__(self, locale, parent=None):
        super().__init__(parent)
        self.setObjectName("homePage")
        self.setStyleSheet("""
            #homePage { background: #101820; }
            #homePage QLabel { color: #f4f7f4; background: transparent; }
            #homePage QFrame#hero, #homePage QFrame#toolCard {
                background: #18242d; border: 1px solid #304a50; border-radius: 20px;
            }
            #homePage QLabel#eyebrow { color: #6fe0c4; font-size: 12px; font-weight: 700; }
            #homePage QLabel#title { font-size: 36px; font-weight: 700; }
            #homePage QLabel#heroTitle { font-size: 28px; font-weight: 700; }
            #homePage QLabel#sectionTitle { font-size: 19px; font-weight: 700; }
            #homePage QLabel#muted, #homePage QLabel#cardDescription {
                color: #b7cbcb; font-size: 13px;
            }
            #homePage QPushButton {
                background: #6fe0c4; color: #102028; border: 0; border-radius: 10px;
                padding: 10px 16px; font-size: 13px; font-weight: 700;
            }
            #homePage QPushButton:hover { background: #94eed6; }
            #homePage QPushButton:focus { border: 2px solid #f8bd83; }
            #homePage QPushButton[variant="secondary"] {
                background: #263a43; color: #f4f7f4; border: 1px solid #4b686b;
            }
            #homePage QPushButton[variant="secondary"]:hover { background: #34505a; }
            #homePage QComboBox {
                background: #263a43; color: #f4f7f4; border: 1px solid #4b686b;
                border-radius: 9px; padding: 8px 12px; min-width: 130px;
            }
        """)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        outer.addWidget(scroll)
        canvas = QWidget()
        canvas.setObjectName("homePage")
        scroll.setWidget(canvas)
        canvas_layout = QVBoxLayout(canvas)
        canvas_layout.setContentsMargins(34, 30, 34, 32)
        canvas_layout.setSpacing(24)

        header = QHBoxLayout()
        heading = QVBoxLayout()
        eyebrow = QLabel(tr("VIDEO WORKSPACE"))
        eyebrow.setObjectName("eyebrow")
        heading.addWidget(eyebrow)
        title = QLabel(tr("Video Workshop"))
        title.setObjectName("title")
        heading.addWidget(title)
        header.addLayout(heading)
        header.addStretch()
        language_area = QVBoxLayout()
        language_label = QLabel(tr("Interface language"))
        language_label.setObjectName("muted")
        language_area.addWidget(language_label)
        self.language = QComboBox()
        for label, code in (("Tiếng Việt", "vi_VN"), ("English", "en_US"), ("中文", "zh_CN")):
            self.language.addItem(label, code)
        self.reset_locale(locale)
        self.language.currentIndexChanged.connect(self._request_locale)
        language_area.addWidget(self.language)
        header.addLayout(language_area)
        canvas_layout.addLayout(header)

        hero = QFrame()
        hero.setObjectName("hero")
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(28, 25, 28, 26)
        hero_layout.setSpacing(12)
        hero_eyebrow = QLabel(tr("FROM VIDEO TO EVERY LANGUAGE"))
        hero_eyebrow.setObjectName("eyebrow")
        hero_layout.addWidget(hero_eyebrow)
        hero_title = QLabel(tr("Make your next video understandable to everyone"))
        hero_title.setObjectName("heroTitle")
        hero_title.setWordWrap(True)
        hero_layout.addWidget(hero_title)
        intro = QLabel(tr("Import media, transcribe speech, translate subtitles and create a new voice in one workspace."))
        intro.setObjectName("muted")
        intro.setWordWrap(True)
        hero_layout.addWidget(intro)
        actions = QHBoxLayout()
        open_workspace = QPushButton(tr("Open video workspace"))
        open_workspace.setObjectName('openWorkspace')
        open_workspace.setAccessibleName(tr("Open video workspace"))
        open_workspace.clicked.connect(self.workspace_requested)
        actions.addWidget(open_workspace)
        translate_srt = QPushButton(tr("Translate SRT"))
        translate_srt.setObjectName('openTranslateSrt')
        translate_srt.setProperty('variant', 'secondary')
        translate_srt.clicked.connect(lambda: self.tool_requested.emit("fn_fanyisrt"))
        actions.addWidget(translate_srt)
        actions.addStretch()
        hero_layout.addLayout(actions)
        canvas_layout.addWidget(hero)

        tools_header = QLabel(tr("Quick tools"))
        tools_header.setObjectName("sectionTitle")
        canvas_layout.addWidget(tools_header)
        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(14)
        cards = (
            ("fn_recogn", "01", "Transcribe speech", "Create SRT subtitles from video or audio."),
            ("fn_fanyisrt", "02", "Translate SRT", "Translate text and subtitle files."),
            ("fn_peiyinrole", "03", "Multiple speakers", "Assign a voice to each subtitle speaker."),
            ("fn_vas", "04", "Merge video, audio and SRT", "Combine your finished media files."),
        )
        for position, (name, number, title_text, description) in enumerate(cards):
            card = QFrame()
            card.setObjectName("toolCard")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(20, 16, 20, 17)
            card_layout.setSpacing(8)
            number_label = QLabel(number)
            number_label.setObjectName("eyebrow")
            card_layout.addWidget(number_label)
            card_title = QLabel(tr(title_text))
            card_title.setObjectName("sectionTitle")
            card_title.setWordWrap(True)
            card_layout.addWidget(card_title)
            detail = QLabel(tr(description))
            detail.setObjectName("cardDescription")
            detail.setWordWrap(True)
            card_layout.addWidget(detail)
            button = QPushButton(tr("Open tool"))
            button.setObjectName(f'open_{name}')
            button.setProperty('variant', 'secondary')
            button.setAccessibleName(f"{tr('Open tool')}: {tr(title_text)}")
            button.clicked.connect(lambda checked=False, tool=name: self.tool_requested.emit(tool))
            card_layout.addWidget(button, alignment=Qt.AlignmentFlag.AlignLeft)
            grid.addWidget(card, position // 2, position % 2)
        canvas_layout.addLayout(grid)
        canvas_layout.addStretch()

    def reset_locale(self, locale):
        index = self.language.findData(locale)
        self.language.blockSignals(True)
        self.language.setCurrentIndex(index if index >= 0 else 0)
        self.language.blockSignals(False)

    def _request_locale(self):
        locale = self.language.currentData()
        if locale:
            self.locale_requested.emit(locale)
