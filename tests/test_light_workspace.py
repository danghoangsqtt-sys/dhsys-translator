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
        for name in ("fn_recogn", "fn_fanyisrt", "fn_peiyinrole", "fn_vas"):
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
    assert len(buttons) == 4
    for button in buttons:
        button.click()
    assert window.triggered == ["fn_recogn", "fn_fanyisrt", "fn_peiyinrole", "fn_vas"]

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
