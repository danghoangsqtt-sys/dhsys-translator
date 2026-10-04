"""Check that every dynamically loaded GUI menu module is in the bundle.

Run as ``sp.exe smoke_dynamic_menus.py report.json``. Importing modules does
not call remote providers or start a media task.
"""

import importlib
import json
from pathlib import Path
import sys
import traceback


SECTIONS = (
    "MENU_CFG_PANEL",
    "MENU_CFG_TRANS",
    "MENU_CFG_TTS",
    "MENU_CFG_STT",
    "MENU_CFG_TOOLS",
    "MENU_CFG_HELP",
)
COMPONENT_WINDOWS = {
    "clip_video", "realtime_stt", "textmatching", "set_ass",
    "formatsrtfiles", "xxl",
}


def main():
    if len(sys.argv) < 2:
        return 2
    report_path = Path(sys.argv[1]).resolve()
    open_windows = "--open" in sys.argv[2:]
    from videotrans.ui import menu_list
    if open_windows:
        from PySide6.QtWidgets import QApplication
        from videotrans.winform import get_win
        app = QApplication.instance() or QApplication([])

    results = []
    for section in SECTIONS:
        for name, title, action in getattr(menu_list, section):
            if action is not None:
                continue
            component = name in COMPONENT_WINDOWS
            modules = [f"videotrans.{'component' if component else 'winform'}.{name}"]
            if not component:
                modules.append(f"videotrans.ui.{name}")
            item = {"section": section, "name": name, "title": title, "modules": modules}
            try:
                for module in modules:
                    importlib.import_module(module)
                if open_windows:
                    window = get_win(name)
                    if window is not None:
                        window.close()
                    app.processEvents()
                item["status"] = "pass"
            except BaseException as error:
                item.update(status="fail", error=str(error), traceback=traceback.format_exc())
            results.append(item)
            if open_windows:
                report_path.parent.mkdir(parents=True, exist_ok=True)
                report_path.write_text(json.dumps({"status": "running", "results": results},
                                                  ensure_ascii=False, indent=2), encoding="utf-8")

    report = {
        "status": "pass" if all(item["status"] == "pass" for item in results) else "fail",
        "frozen": bool(getattr(sys, "frozen", False)),
        "opened": open_windows,
        "results": results,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
