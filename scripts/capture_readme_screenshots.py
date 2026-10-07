"""Capture deterministic README screenshots from the current Qt widgets.

The script intentionally uses sample labels and a synthetic readiness report so
that committed images never contain local file paths, media or credentials.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("PYVIDEOTRANS_LANG", "vi")

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QApplication, QMainWindow

from videotrans.configure._paths import resource_path
from videotrans.configure.config import defaulelang
from videotrans.diagnostics.system_readiness import (
    GIB,
    NvidiaProbe,
    ProbeSnapshot,
    evaluate_readiness,
)
from videotrans.ui.en import Ui_MainWindow
from videotrans.ui.home import HomePage
from videotrans.ui.systemcheck import Ui_systemcheck
from videotrans.ui.workspace_shell import WorkspaceShell


class _GeneratedWindow(QMainWindow, Ui_MainWindow):
    def show_home(self):
        """WorkspaceShell requires the same route exposed by MainWindow."""


def _save_widget(app: QApplication, widget, path: Path, size: tuple[int, int]) -> None:
    widget.resize(*size)
    widget.show()
    app.processEvents()
    image = widget.grab()
    if image.isNull() or not image.save(str(path), "PNG"):
        raise RuntimeError(f"Could not save screenshot: {path}")
    widget.close()
    app.processEvents()


def _sample_readiness_report():
    return evaluate_readiness(
        ProbeSnapshot(
            os_name="Windows",
            os_release="11",
            architecture="AMD64",
            cpu_logical_count=16,
            ram_bytes=32 * GIB,
            disk_free_bytes=180 * GIB,
            ffmpeg_present=True,
            ffprobe_present=True,
            resources_present=True,
            user_data_writable=True,
            cache_writable=True,
            nvidia=NvidiaProbe(
                state="ok",
                gpu_count=1,
                total_vram_mib=8192,
                cuda_driver_version="12.8",
            ),
        )
    )


def capture(output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication([])
    app.setApplicationName("pyVideoTrans-DH README capture")
    # The offscreen Windows plugin may otherwise select a legacy font without
    # Vietnamese glyphs even though the interactive app renders them normally.
    font_dir = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
    loaded_families: list[str] = []
    for filename in ("segoeui.ttf", "segoeuib.ttf"):
        font_id = QFontDatabase.addApplicationFont(str(font_dir / filename))
        if font_id >= 0:
            loaded_families.extend(QFontDatabase.applicationFontFamilies(font_id))
    app.setFont(QFont(loaded_families[0] if loaded_families else "Segoe UI", 10))
    app.setStyleSheet(
        resource_path("videotrans", "styles", "light.qss").read_text(encoding="utf-8")
    )

    home = HomePage(defaulelang)
    home_path = output_dir / "home-vi.png"
    _save_widget(app, home, home_path, (1440, 900))

    window = _GeneratedWindow()
    window.setupUi(window)
    window.subtitle_area.setPlainText(
        "1\n00:00:01,000 --> 00:00:04,000\n"
        "Phụ đề và bản xem trước xuất hiện tại đây."
    )
    workspace = WorkspaceShell(window, window.takeCentralWidget())
    workspace_path = output_dir / "workspace-vi.png"
    _save_widget(app, workspace, workspace_path, (1440, 900))
    window.close()

    system_check = Ui_systemcheck(locale="vi_VN", auto_refresh=False)
    system_check.set_report(_sample_readiness_report())
    system_check_path = output_dir / "system-check-vi.png"
    _save_widget(app, system_check, system_check_path, (900, 860))

    return [home_path, workspace_path, system_check_path]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Capture sanitized Qt screenshots used by README.md."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPO_ROOT / "docs" / "assets" / "readme",
    )
    args = parser.parse_args()
    for path in capture(args.output_dir.resolve()):
        print(path.relative_to(REPO_ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
