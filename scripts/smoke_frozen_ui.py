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

    from PySide6.QtWidgets import QApplication, QPushButton
    from videotrans.configure.config import defaulelang, tr
    from videotrans.configure._paths import resource_path
    from videotrans.ui.home import HomePage
    from videotrans.ui.info import Ui_info

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
    return {'locale': defaulelang, 'brand': tr('Video Workshop'), 'routes': routes}


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
