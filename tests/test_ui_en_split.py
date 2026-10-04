from PySide6.QtWidgets import QApplication, QMainWindow

from videotrans.ui.en import Ui_MainWindow
from videotrans.ui.menu_list import (
    MENU_CFG_TRANS, MENU_CFG_TTS, MENU_CFG_STT,
    MENU_CFG_TOOLS, MENU_CFG_HELP, MENU_CFG_PANEL,
)


app = QApplication.instance() or QApplication([])


class _TestWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)


def test_setup_ui_creates_core_workflow_controls():
    win = _TestWindow()
    for name in (
        "btn_get_video", "source_mp4", "btn_save_dir", "recogn_type",
        "translate_type", "tts_type", "source_language", "target_language",
        "subtitle_type", "startbtn", "retrybtn", "output_dir",
        "menuBar", "toolBar", "statusBar",
    ):
        assert getattr(win, name, None) is not None, f"Missing control: {name}"


def test_menu_actions_follow_configuration():
    win = _TestWindow()
    for menu, menu_config in (
        (win.menu_Key, MENU_CFG_TRANS), (win.menu_TTS, MENU_CFG_TTS),
        (win.menu_RECOGN, MENU_CFG_STT), (win.menu, MENU_CFG_TOOLS),
        (win.menu_H, MENU_CFG_HELP), (win.toolBar, MENU_CFG_PANEL),
    ):
        for key, title, _ in menu_config:
            action = getattr(win, key)
            assert action.objectName() == key
            assert action.text() == title
            assert action in menu.actions()


def test_labels_and_mode_actions_have_text():
    win = _TestWindow()
    for control in (win.btn_get_video, win.btn_save_dir, win.startbtn, win.tts_text):
        assert control.text()
    for action in (win.action_biaozhun, win.action_tiquzimu):
        assert action.text()
        assert action.toolTip()
