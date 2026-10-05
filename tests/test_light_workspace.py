from pathlib import Path

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication, QMainWindow, QMenu, QToolBar, QWidget

from videotrans.ui.en import Ui_MainWindow
from videotrans.ui.workspace_shell import WorkspaceShell


app = QApplication.instance() or QApplication([])


class _WindowDouble(QMainWindow):
    def __init__(self):
        super().__init__()
        self.home_calls = 0
        self.triggered = []
        self.menu = self.menuBar().addMenu("Settings")
        self.menu_action = QAction("Provider settings", self)
        self.menu.addAction(self.menu_action)
        self.toolBar = QToolBar(self)
        self.addToolBar(self.toolBar)
        for name in ("action_biaozhun", "fn_recogn", "fn_fanyisrt", "fn_peiyin", "fn_vas"):
            action = QAction(name, self)
            action.triggered.connect(lambda checked=False, item=name: self.triggered.append(item))
            setattr(self, name, action)
            self.toolBar.addAction(action)

    def show_home(self):
        self.home_calls += 1


def test_workspace_shell_retains_original_workspace_and_actions():
    window = _WindowDouble()
    workspace = QWidget()
    workspace.setObjectName("originalWorkspace")
    shell = WorkspaceShell(window, workspace)

    assert shell.findChild(QWidget, "originalWorkspace") is workspace
    buttons = shell.findChildren(QWidget, "workspaceQuickAction")
    assert len(buttons) == 5
    for button in buttons:
        button.click()
    assert window.triggered == ["action_biaozhun", "fn_recogn", "fn_fanyisrt", "fn_peiyin", "fn_vas"]

    catalog = shell.all_tools.menu()
    catalog_actions = {
        action for section in shell._catalog_sections for action in section.actions()
    }
    assert set(window.toolBar.actions()) <= catalog_actions
    assert window.menu_action in catalog_actions


def test_light_qss_has_approved_tokens_and_primary_control_rules():
    qss = (Path(__file__).resolve().parents[1] / "videotrans" / "styles" / "light.qss").read_text(encoding="utf-8")
    assert "#14452F" in qss
    assert "QPushButton#startbtn" in qss
    assert "QMenuBar" in qss
    assert 'QFrame[workflowSection="true"]' in qss
    assert 'QFrame[workflowSection="true"][workflowState="running"]' in qss
    assert 'QLabel#workflowStatus[workflowState="error"]' in qss
    assert "QFrame#workflowActionArea" in qss
    assert "QFrame#workflowActivityArea" in qss
    assert "QLabel#workflowStepBadge" in qss
    assert "QLabel#subtitlePanelTitle" in qss
    assert "QToolButton#workspaceCompactNavigation" in qss


def test_workspace_shell_accepts_generated_menu_bar_attribute():
    class GeneratedWindow(QMainWindow, Ui_MainWindow):
        def show_home(self):
            pass

    window = GeneratedWindow()
    window.setupUi(window)
    workspace = window.takeCentralWidget()
    shell = WorkspaceShell(window, workspace)

    assert shell.all_tools.menu() is not None
    assert window.fn_fanyisrt in {
        action for section in shell._catalog_sections for action in section.actions()
    }


def test_workspace_shell_compacts_navigation_on_narrow_desktop_width():
    window = _WindowDouble()
    shell = WorkspaceShell(window, QWidget())
    shell.resize(900, 700)
    shell.show()
    app.processEvents()

    assert shell.sidebar.isHidden()
    assert shell.compact_navigation.isVisible()
    assert all(
        getattr(window, name) in shell.compact_navigation.menu().actions()
        for name in ("action_biaozhun", "fn_recogn", "fn_fanyisrt", "fn_peiyin", "fn_vas")
    )

    shell.resize(1200, 700)
    app.processEvents()
    assert shell.sidebar.isVisible()
    assert shell.compact_navigation.isHidden()


def test_provider_actions_are_reachable_from_settings_but_absent_from_media_catalog():
    window = _WindowDouble()
    window.menu_Key = window.menuBar().addMenu("Translation providers")
    window.menu_TTS = window.menuBar().addMenu("TTS providers")
    window.menu_RECOGN = window.menuBar().addMenu("STT providers")
    provider_actions = []
    for menu, label in (
        (window.menu_Key, "Gemini"),
        (window.menu_TTS, "Edge TTS"),
        (window.menu_RECOGN, "faster-whisper"),
    ):
        action = QAction(label, window)
        menu.addAction(action)
        provider_actions.append(action)

    shell = WorkspaceShell(window, QWidget())
    catalog_actions = {
        action for section in shell._catalog_sections for action in section.actions()
    }
    settings_actions = {
        action for section in shell._provider_sections for action in section.actions()
    }

    assert not set(provider_actions) & catalog_actions
    assert set(provider_actions) <= settings_actions
    assert set(window.toolBar.actions()) <= catalog_actions
