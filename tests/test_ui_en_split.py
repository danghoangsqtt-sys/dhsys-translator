from PySide6.QtWidgets import QApplication, QMainWindow

from videotrans.ui.en import Ui_MainWindow
from videotrans.ui.workflow_state import WORKFLOW_RUNNING
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


def test_existing_rows_are_grouped_into_five_workflow_sections():
    win = _TestWindow()
    expected = {
        "prepareSection": "workflowPrepare",
        "transcriptionSection": "workflowTranscription",
        "translationSection": "workflowTranslation",
        "voiceSection": "workflowVoice",
        "outputSection": "workflowOutput",
    }
    for attribute, object_name in expected.items():
        section = getattr(win, attribute)
        assert section.objectName() == object_name
        assert section.property("workflowSection") is True

    assert win.btn_get_video.parentWidget() is win.prepareSection
    assert win.recogn_type.parentWidget() is win.transcriptionSection
    assert win.translate_type.parentWidget() is win.translationSection
    assert win.tts_type.parentWidget() is win.voiceSection
    assert win.subtitle_type.parentWidget() is win.outputSection


def test_workflow_view_state_updates_existing_cards_without_replacing_controls():
    win = _TestWindow()
    win.set_workflow_view_state(WORKFLOW_RUNNING)

    assert win.workflowStatus.property("workflowState") == WORKFLOW_RUNNING
    for section in (
        win.prepareSection,
        win.transcriptionSection,
        win.translationSection,
        win.voiceSection,
        win.outputSection,
    ):
        assert section.property("workflowState") == WORKFLOW_RUNNING
    assert win.btn_get_video.parentWidget() is win.prepareSection
    assert win.recogn_type.parentWidget() is win.transcriptionSection


def test_workflow_hierarchy_groups_existing_action_activity_and_subtitle_widgets():
    win = _TestWindow()

    assert win.workflowActionArea.objectName() == "workflowActionArea"
    assert win.startbtn.parentWidget() is win.workflowActionArea
    assert win.retrybtn.parentWidget() is win.workflowActionArea
    assert win.output_dir.parentWidget() is win.workflowActionArea
    assert win.workflowActivityArea.objectName() == "workflowActivityArea"
    assert win.scroll_area.parentWidget() is win.workflowActivityArea
    assert win.subtitlePanelTitle.parentWidget() is win.verticalLayoutWidget
    assert win.subtitle_area.parentWidget() is win.verticalLayoutWidget
    assert win.import_subtitle.parentWidget() is win.verticalLayoutWidget

    badges = win.findChildren(type(win.workflowActivityTitle), "workflowStepBadge")
    assert [badge.text() for badge in badges] == ["1", "2", "3", "4", "5"]


def test_workflow_rows_wrap_inside_a_narrow_desktop_pane():
    win = _TestWindow()
    win.resize(1024, 720)
    win.show()
    app.processEvents()

    assert win.workflowScroll.widget() is win.layoutWidget
    assert win.workflowScroll.verticalScrollBarPolicy().name == "ScrollBarAsNeeded"
    transcription_row = win.transcriptionSection.layout().itemAt(1).layout()
    assert transcription_row.heightForWidth(440) > transcription_row.heightForWidth(900)

    for section in (
        win.prepareSection,
        win.transcriptionSection,
        win.translationSection,
        win.voiceSection,
        win.outputSection,
    ):
        for child in section.findChildren(type(win.btn_get_video)):
            if child.isVisible():
                assert child.geometry().right() < section.width()
