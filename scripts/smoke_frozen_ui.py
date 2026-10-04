"""Verify the packaged Vietnamese start page and its navigation signals."""

import json
import os
from pathlib import Path
import sys
import traceback


def run_check():
    if not getattr(sys, 'frozen', False):
        raise AssertionError('run this probe through the packaged sp.exe')
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    os.environ['PYVIDEOTRANS_LANG'] = 'vi'

    from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton
    from videotrans.configure.config import defaulelang, tr
    from videotrans.configure._paths import resource_path
    from videotrans.ui.home import HomePage
    from videotrans.ui.info import Ui_info
    from videotrans.ui.en import Ui_MainWindow
    from videotrans.ui.workspace_shell import WorkspaceShell

    app = QApplication.instance() or QApplication([])
    if defaulelang != 'vi_VN' or tr('Video Workshop') != 'Xưởng Video':
        raise AssertionError(f'Vietnamese locale failed: {defaulelang}')
    if not resource_path('videotrans', 'language', 'vi_VN.json').is_file():
        raise AssertionError('Vietnamese catalog missing from package')

    page = HomePage(defaulelang)
    page.show()
    app.processEvents()
    routes = []
    workspaces = []
    page.tool_requested.connect(routes.append)
    page.workspace_requested.connect(lambda: workspaces.append(True))
    page.findChild(QPushButton, 'openWorkspace').click()
    for name in ('fn_recogn', 'fn_fanyisrt', 'fn_peiyinrole', 'fn_vas'):
        page.findChild(QPushButton, f'open_{name}').click()
    if routes != ['fn_recogn', 'fn_fanyisrt', 'fn_peiyinrole', 'fn_vas'] or workspaces != [True]:
        raise AssertionError(f'home navigation failed: {routes}, {workspaces}')
    about = Ui_info()
    if 'pyvideotrans.com' in about.windowTitle().lower():
        raise AssertionError('legacy website appears in About title')
    about.close()
    page.close()

    class GeneratedWindow(QMainWindow, Ui_MainWindow):
        def show_home(self):
            pass

    window = GeneratedWindow()
    window.setupUi(window)
    workspace = window.takeCentralWidget()
    shell = WorkspaceShell(window, workspace)
    catalog_actions = {
        action for section in shell._catalog_sections for action in section.actions()
    }
    workflow_sections = (
        window.prepareSection,
        window.transcriptionSection,
        window.translationSection,
        window.voiceSection,
        window.outputSection,
    )
    if shell.findChild(type(workspace), 'centralwidget') is not workspace or window.fn_fanyisrt not in catalog_actions:
        raise AssertionError('packaged workspace shell did not retain original actions')
    if any(section.property('workflowSection') is not True for section in workflow_sections):
        raise AssertionError('packaged workspace is missing a workflow section')
    if (window.btn_get_video.parentWidget() is not window.prepareSection
            or window.recogn_type.parentWidget() is not window.transcriptionSection
            or window.translate_type.parentWidget() is not window.translationSection
            or window.tts_type.parentWidget() is not window.voiceSection
            or window.subtitle_type.parentWidget() is not window.outputSection):
        raise AssertionError('packaged workflow controls are not in their intended sections')
    if (window.startbtn.parentWidget() is not window.workflowActionArea
            or window.retrybtn.parentWidget() is not window.workflowActionArea
            or window.scroll_area.parentWidget() is not window.workflowActivityArea
            or window.subtitle_area.parentWidget() is not window.verticalLayoutWidget):
        raise AssertionError('packaged workspace hierarchy did not retain existing controls')
    shell.resize(900, 720)
    shell.show()
    app.processEvents()
    transcription_row = window.transcriptionSection.layout().itemAt(1).layout()
    if (not shell.sidebar.isHidden() or not shell.compact_navigation.isVisible()
            or window.workflowScroll.widget() is not window.layoutWidget
            or transcription_row.heightForWidth(440) <= transcription_row.heightForWidth(900)):
        raise AssertionError('packaged workspace does not adapt to a narrow desktop width')
    window.set_workflow_view_state('running')
    if (window.workflowStatus.property('workflowState') != 'running'
            or any(section.property('workflowState') != 'running' for section in workflow_sections)):
        raise AssertionError('packaged workflow view state did not reach every section')
    window.close()
    return {
        'locale': defaulelang,
        'brand': tr('Video Workshop'),
        'routes': routes,
        'workspace_shell': True,
        'light_style': resource_path('videotrans', 'styles', 'light.qss').is_file(),
        'workflow_sections': len(workflow_sections),
        'workflow_state': 'running',
        'workflow_hierarchy': True,
        'responsive_layout': True,
    }


def main():
    if len(sys.argv) < 2:
        return 2
    report_path = Path(sys.argv[1]).resolve()
    try:
        report = {'status': 'pass', 'checks': run_check()}
        status = 0
    except BaseException as error:
        report = {'status': 'fail', 'error': str(error), 'traceback': traceback.format_exc()}
        status = 1
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    return status


if __name__ == '__main__':
    raise SystemExit(main())
