"""Open every dynamic left-sidebar window in a packaged Windows candidate.

Run as ``sp.exe smoke_sidebar.py report.json`` from outside the install tree.
No provider requests or media processing are started.
"""

import importlib
import json
import os
from pathlib import Path
import sys
import traceback


def main():
    if len(sys.argv) < 2:
        return 2
    report_path = Path(sys.argv[1]).resolve()
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    from PySide6.QtWidgets import QApplication
    from videotrans.ui.menu_list import MENU_CFG_PANEL
    from videotrans.winform import get_win

    app = QApplication.instance() or QApplication([])
    results = []
    for name, title, action in MENU_CFG_PANEL:
        if action is not None:
            continue
        item = {"name": name, "title": title}
        try:
            for module_name in (f"videotrans.winform.{name}", f"videotrans.ui.{name}"):
                importlib.import_module(module_name)
            window = get_win(name)
            if window is not None:
                window.close()
            app.processEvents()
            item["status"] = "pass"
        except BaseException as error:
            item.update(status="fail", error=str(error), traceback=traceback.format_exc())
        results.append(item)

    report = {
        "status": "pass" if all(item["status"] == "pass" for item in results) else "fail",
        "frozen": bool(getattr(sys, "frozen", False)),
        "results": results,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
