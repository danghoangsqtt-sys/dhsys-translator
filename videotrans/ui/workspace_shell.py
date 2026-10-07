"""Presentation shell for the existing video workspace.

The shell deliberately reuses the actions and central widget created by
``Ui_MainWindow``. It owns no media-processing behavior.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox, QFrame, QHBoxLayout, QLabel, QMenu, QMessageBox, QPushButton, QToolButton,
    QVBoxLayout, QWidget,
)

from videotrans.configure.config import params, tr
from videotrans.ui.provider_profiles import (
    PROFILE_BY_KEY,
    PROFILE_CUSTOM,
    PROFILE_LOCAL,
    PROFILES,
    profile_policy,
)


class WorkspaceShell(QWidget):
    """Light navigation and hierarchy around an already-built workspace."""

    COMPACT_BREAKPOINT = 980

    BASIC_JOBS = (
        ("action_biaozhun", "Create translated video"),
        ("fn_recogn", "Transcribe to SRT"),
        ("fn_fanyisrt", "Translate SRT"),
        ("fn_peiyin", "Create voice audio"),
        ("fn_vas", "Merge/export video"),
    )

    def __init__(self, main_window, workspace, parent=None):
        super().__init__(parent)
        self.setObjectName("workspaceShell")
        self.main_window = main_window
        self.workspace = workspace
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self.sidebar = self._build_sidebar()
        root.addWidget(self.sidebar)
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
        tools_label = QLabel(tr("Media jobs"))
        tools_label.setObjectName("workspaceGroup")
        layout.addWidget(tools_label)
        for action_name, label in self.BASIC_JOBS:
            button = QPushButton(tr(label))
            button.setObjectName("workspaceQuickAction")
            button.setAccessibleName(tr(label))
            action = getattr(self.main_window, action_name)
            button.clicked.connect(action.trigger)
            layout.addWidget(button)
        profile_label = QLabel(tr("Provider profile"))
        profile_label.setObjectName("workspaceGroup")
        layout.addWidget(profile_label)
        self.provider_profile = QComboBox(sidebar)
        self.provider_profile.setObjectName("workspaceProviderProfile")
        for profile in PROFILES:
            self.provider_profile.addItem(tr(profile.label_key), profile.key)
        active_profile = (
            self.main_window.current_provider_profile()
            if hasattr(self.main_window, "current_provider_profile") else PROFILE_CUSTOM
        )
        self.set_provider_profile(active_profile)
        self.provider_profile.currentIndexChanged.connect(self._request_provider_profile)
        self.provider_profile.setEnabled(hasattr(self.main_window, "apply_provider_profile"))
        layout.addWidget(self.provider_profile)
        self.profile_hint = QLabel()
        self.profile_hint.setObjectName("workspaceProfileHint")
        self.profile_hint.setWordWrap(True)
        layout.addWidget(self.profile_hint)
        self._update_profile_hint(active_profile)
        self.provider_settings = QToolButton(sidebar)
        self.provider_settings.setObjectName("workspaceProviderSettings")
        self.provider_settings.setText(tr("Provider settings"))
        self.provider_settings.setToolTip(tr("Provider visibility guidance"))
        self.provider_settings.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        self.provider_settings.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.provider_settings.setMenu(self._build_provider_settings())
        layout.addWidget(self.provider_settings)
        catalog_label = QLabel(tr("Advanced tools"))
        catalog_label.setObjectName("workspaceGroup")
        layout.addWidget(catalog_label)
        self.all_tools = QToolButton()
        self.all_tools.setObjectName("workspaceAllTools")
        self.all_tools.setText(tr("Open advanced tools"))
        self.all_tools.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        self.all_tools.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.all_tools.setMenu(self._build_action_catalog())
        layout.addWidget(self.all_tools)
        systemcheck_action = getattr(self.main_window, "systemcheck", None)
        if systemcheck_action is not None:
            self.system_check = QToolButton(sidebar)
            self.system_check.setObjectName("workspaceSystemCheck")
            self.system_check.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
            self.system_check.setDefaultAction(systemcheck_action)
            layout.addWidget(self.system_check)
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
        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        title_copy = QVBoxLayout()
        title_copy.setContentsMargins(0, 0, 0, 0)
        title_copy.setSpacing(3)
        eyebrow = QLabel(tr("VIDEO WORKSPACE"))
        eyebrow.setObjectName("workspaceEyebrow")
        title_copy.addWidget(eyebrow)
        title = QLabel(tr("Video Workspace"))
        title.setObjectName("workspaceTitle")
        title_copy.addWidget(title)
        title_row.addLayout(title_copy, 1)
        self.compact_navigation = QToolButton(header)
        self.compact_navigation.setObjectName("workspaceCompactNavigation")
        self.compact_navigation.setText(tr("Menu"))
        self.compact_navigation.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        self.compact_navigation.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.compact_navigation.setMenu(self._build_compact_navigation_menu())
        self.compact_navigation.setVisible(False)
        title_row.addWidget(self.compact_navigation, 0, Qt.AlignmentFlag.AlignTop)
        header_layout.addLayout(title_row)
        subtitle = QLabel(tr("Choose media, configure the steps, then start processing."))
        subtitle.setObjectName("workspaceSubtitle")
        subtitle.setWordWrap(True)
        header_layout.addWidget(subtitle)
        layout.addWidget(header)
        layout.addWidget(self.workspace, 1)
        return content

    def _build_compact_navigation_menu(self):
        """Expose the same workspace actions when the full sidebar is hidden."""
        menu = QMenu(self)
        home = menu.addAction(tr("Home"))
        home.triggered.connect(self.main_window.show_home)
        menu.addSection(tr("Media jobs"))
        for action_name, _ in self.BASIC_JOBS:
            menu.addAction(getattr(self.main_window, action_name))
        systemcheck_action = getattr(self.main_window, "systemcheck", None)
        if systemcheck_action is not None:
            menu.addSeparator()
            menu.addAction(systemcheck_action)
        menu.addSeparator()
        advanced = menu.addMenu(tr("Advanced tools"))
        self._populate_action_catalog(advanced)
        providers = menu.addMenu(tr("Provider settings"))
        self._populate_provider_settings(providers)
        return menu

    def resizeEvent(self, event):
        compact = self.width() < self.COMPACT_BREAKPOINT
        self.sidebar.setVisible(not compact)
        self.compact_navigation.setVisible(compact)
        super().resizeEvent(event)

    def _build_action_catalog(self):
        """Expose media/help actions without mixing in provider configuration."""
        catalog = QMenu(self)
        self._catalog_sections = []
        self._populate_action_catalog(catalog, self._catalog_sections)
        return catalog

    def _populate_action_catalog(self, catalog, tracked_sections=None):
        workspace_actions = self.main_window.toolBar.actions()
        if workspace_actions:
            section = catalog.addMenu(tr("Workspace actions"))
            if tracked_sections is not None:
                tracked_sections.append(section)
            section.addActions(workspace_actions)
        menu_bar = self.main_window.menuBar
        if callable(menu_bar):
            menu_bar = menu_bar()
        provider_menus = {
            getattr(self.main_window, name, None)
            for name in ("menu_Key", "menu_TTS", "menu_RECOGN")
        }
        for menu_action in menu_bar.actions():
            source_menu = menu_action.menu()
            if source_menu is None or source_menu in provider_menus:
                continue
            section = catalog.addMenu(menu_action.text())
            if tracked_sections is not None:
                tracked_sections.append(section)
            section.addActions(source_menu.actions())

    def _build_provider_settings(self):
        menu = QMenu(self)
        self._provider_sections = []
        self._populate_provider_settings(menu, self._provider_sections)
        return menu

    def _populate_provider_settings(self, menu, tracked_sections=None):
        if not hasattr(self, "_provider_menu_data"):
            self._provider_menu_data = []
            for name in ("menu_RECOGN", "menu_Key", "menu_TTS"):
                source = getattr(self.main_window, name, None)
                if source is not None:
                    self._provider_menu_data.append((source.title(), tuple(source.actions())))
        for title, actions in self._provider_menu_data:
            section = menu.addMenu(title)
            if tracked_sections is not None:
                tracked_sections.append(section)
            section.addActions(actions)

    def set_provider_profile(self, profile_key):
        if profile_key not in PROFILE_BY_KEY:
            profile_key = PROFILE_CUSTOM
        if not hasattr(self, "provider_profile"):
            return
        index = self.provider_profile.findData(profile_key)
        self.provider_profile.blockSignals(True)
        self.provider_profile.setCurrentIndex(index)
        self.provider_profile.blockSignals(False)
        self._update_profile_hint(profile_key)

    def _update_profile_hint(self, profile_key):
        if not hasattr(self, "profile_hint"):
            return
        profile = PROFILE_BY_KEY.get(profile_key, PROFILE_BY_KEY[PROFILE_CUSTOM])
        policy = profile_policy(profile.key, params.get("localllm_api", ""))
        self.profile_hint.setText(tr(profile.hint_key) + "\n" + tr(policy.summary_key))

    def _request_provider_profile(self):
        profile_key = self.provider_profile.currentData()
        profile = PROFILE_BY_KEY.get(profile_key)
        if profile is None:
            return
        previous = self.main_window.current_provider_profile()
        if profile_key == previous:
            self._update_profile_hint(profile_key)
            return
        policy = profile_policy(profile_key, params.get("localllm_api", ""))
        if profile_key == PROFILE_LOCAL and not policy.local_only_ready:
            QMessageBox.warning(
                self,
                tr("Local profile not ready"),
                tr(policy.summary_key) + "\n\n" + tr("Configure a loopback Local LLM endpoint first."),
            )
            self.set_provider_profile(previous)
            return
        reply = QMessageBox.question(
            self,
            tr("Change provider profile?"),
            tr(profile.hint_key) + "\n" + tr(policy.summary_key) + "\n\n" + tr("Apply this profile now?"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            self.set_provider_profile(previous)
            return
        self.main_window.apply_provider_profile(profile_key)
