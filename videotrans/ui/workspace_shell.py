"""Presentation shell for the existing video workspace.

The shell deliberately reuses the actions and central widget created by
``Ui_MainWindow``. It owns no media-processing behavior.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QMenu, QPushButton, QToolButton,
    QVBoxLayout, QWidget,
)

from videotrans.configure.config import tr


class WorkspaceShell(QWidget):
    """Light navigation and hierarchy around an already-built workspace."""

    QUICK_ACTIONS = (
        ("fn_recogn", "Speech Recognition Text"),
        ("fn_fanyisrt", "Text  Or Srt  Translation"),
        ("fn_peiyinrole", "Multi voice dubbing for SRT"),
        ("fn_vas", "Video Subtitles Merging"),
    )

    def __init__(self, main_window, workspace, parent=None):
        super().__init__(parent)
        self.setObjectName("workspaceShell")
        self.main_window = main_window
        self.workspace = workspace
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_sidebar())
        root.addWidget(self._build_content(), 1)

    def _build_sidebar(self):
        sidebar = QFrame(self)
        sidebar.setObjectName("workspaceSidebar")
        sidebar.setMinimumWidth(218)
        sidebar.setMaximumWidth(250)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 18, 16, 18)
        layout.setSpacing(6)
        brand = QLabel("DHSYSTEM.SYS")
        brand.setObjectName("workspaceBrand")
        layout.addWidget(brand)
        credit = QLabel(tr("Video Workspace"))
        credit.setObjectName("workspaceCredit")
        layout.addWidget(credit)
        layout.addSpacing(14)
        home = QPushButton(tr("Home"))
        home.setObjectName("workspaceHome")
        home.clicked.connect(self.main_window.show_home)
        layout.addWidget(home)
        tools_label = QLabel(tr("Quick tools"))
        tools_label.setObjectName("workspaceGroup")
        layout.addWidget(tools_label)
        for action_name, label in self.QUICK_ACTIONS:
            button = QPushButton(tr(label))
            button.setObjectName("workspaceQuickAction")
            button.setAccessibleName(tr(label))
            action = getattr(self.main_window, action_name)
            button.clicked.connect(action.trigger)
            layout.addWidget(button)
        catalog_label = QLabel(tr("All tools"))
        catalog_label.setObjectName("workspaceGroup")
        layout.addWidget(catalog_label)
        self.all_tools = QToolButton()
        self.all_tools.setObjectName("workspaceAllTools")
        self.all_tools.setText(tr("Open tool catalog"))
        self.all_tools.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        self.all_tools.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.all_tools.setMenu(self._build_action_catalog())
        layout.addWidget(self.all_tools)
        layout.addStretch()
        return sidebar

    def _build_content(self):
        content = QFrame(self)
        content.setObjectName("workspaceContent")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(22, 18, 22, 22)
        layout.setSpacing(14)
        header = QFrame()
        header.setObjectName("workspaceHeader")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(18, 14, 18, 14)
        header_layout.setSpacing(3)
        eyebrow = QLabel(tr("VIDEO WORKSPACE"))
        eyebrow.setObjectName("workspaceEyebrow")
        header_layout.addWidget(eyebrow)
        title = QLabel(tr("Video Workspace"))
        title.setObjectName("workspaceTitle")
        header_layout.addWidget(title)
        subtitle = QLabel(tr("Choose media, configure the steps, then start processing."))
        subtitle.setObjectName("workspaceSubtitle")
        subtitle.setWordWrap(True)
        header_layout.addWidget(subtitle)
        layout.addWidget(header)
        layout.addWidget(self.workspace, 1)
        return content

    def _build_action_catalog(self):
        """Expose existing menu actions again without assigning new handlers."""
        catalog = QMenu(self)
        self._catalog_sections = []
        workspace_actions = self.main_window.toolBar.actions()
        if workspace_actions:
            section = catalog.addMenu(tr("Workspace actions"))
            self._catalog_sections.append(section)
            section.addActions(workspace_actions)
        menu_bar = self.main_window.menuBar
        if callable(menu_bar):
            menu_bar = menu_bar()
        for menu_action in menu_bar.actions():
            source_menu = menu_action.menu()
            if source_menu is None:
                continue
            section = catalog.addMenu(menu_action.text())
            self._catalog_sections.append(section)
            section.addActions(source_menu.actions())
        return catalog
