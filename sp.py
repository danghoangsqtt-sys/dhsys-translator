"""
pyVideoTrans: Translate the video from one language to another and add dubbing

Home-page: https://github.com/jianchang512/pyvideotrans
Author: jianchang512@gmail.com
Documents: https://pyvideotrans.com
Discuss: https://bbs.pyvideotrans.com
License: GPL-V3 <https://www.gnu.org/licenses/gpl-3.0.html>

Code need not be elegant, as long as it runs.
Form need not be fancy, compatibility is enough.
Full of messy code, bugs everywhere.
Global variables tangled like hemp, if-branches stacked like towers.
Eight or nine thread queues, all parameters passed via big dicts.
Can stuff in hardware, wrestle with the system.
No unit tests, no type discipline.
Startup takes three hundred seconds, UI ugly as hell.
Whisper hangs processes before, FFmpeg errors after.
Runs on all three platforms, ten thousand stars and counting.
AI mocks: worst code seen in my life.
Author says: it runs, doesn't it?

"""

import json
import os
import atexit, sys, time
from PySide6.QtWidgets import (QApplication, QFrame, QHBoxLayout, QLabel,
                               QMessageBox, QProgressBar, QVBoxLayout, QWidget)
from PySide6.QtCore import Qt, QRectF, qInstallMessageHandler, QTimer
from PySide6.QtGui import QColor, QGuiApplication, QIcon, QPainter, QPen
import argparse
import tempfile
from pathlib import Path
from PySide6.QtCore import QSize, QSettings
import traceback

# Configuration initializes its locale on import, so read this flag first.
_language_parser = argparse.ArgumentParser(add_help=False)
_language_parser.add_argument('--lang', type=str)
_language_args, _ = _language_parser.parse_known_args()
if _language_args.lang:
    os.environ['PYVIDEOTRANS_LANG'] = _language_args.lang

from videotrans import VERSION
from videotrans.configure._paths import resource_path, LOGS_DIR, ROOT_DIR


# Suppress warnings
def suppress_qt_warnings(msg_type, context, message):
    if "QThreadStorage" in message:
        return


def cleanup():
    """Force cleanup function"""
    try:
        if 'app' in globals():
            app.quit()
    except:
        pass


def show_global_error_dialog(exctype, value, tb):
    tb_str = "".join(traceback.format_exception(exctype, value, tb))
    title = {'vi_VN': 'Lỗi'}.get(_splash_locale(), 'Error')
    QMessageBox.critical(None, title, tb_str)


# Splash screen text is intentionally available before the main configuration import.
_SPLASH_COPY = {
    'vi_VN': {
        'brand': 'XƯỞNG VIDEO',
        'top': 'KHÔNG GIAN BIÊN TẬP',
        'eyebrow': 'ÂM THANH · NGÔN NGỮ · HÌNH ẢNH',
        'title': 'Biến nội dung thành câu chuyện cho mọi ngôn ngữ.',
        'loading': 'Đang chuẩn bị không gian làm việc',
        'ready': 'Sẵn sàng',
    },
    'en_US': {
        'brand': 'VIDEO WORKSHOP',
        'top': 'CREATIVE WORKSPACE',
        'eyebrow': 'AUDIO · LANGUAGE · IMAGE',
        'title': 'Make your story understandable in every language.',
        'loading': 'Preparing your workspace',
        'ready': 'Ready',
    },
}


def _splash_locale():
    lang = os.environ.get('PYVIDEOTRANS_LANG')
    if not lang:
        try:
            cfg_path = Path(ROOT_DIR) / 'videotrans' / 'cfg.json'
            lang = json.loads(cfg_path.read_text(encoding='utf-8')).get('lang')
        except (OSError, ValueError, AttributeError):
            pass
    aliases = {'vi': 'vi_VN', 'vi-vn': 'vi_VN', 'en': 'en_US',
               'en-us': 'en_US', 'zh': 'en_US', 'zh-cn': 'en_US',
               'zh-tw': 'en_US'}
    selected = aliases.get(str(lang).strip().lower().replace('_', '-'), lang)
    return selected if selected in _SPLASH_COPY else 'vi_VN'


class SplashArtwork(QWidget):
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.translate(self.width() / 2, self.height() / 2)
        painter.rotate(-10)
        for offset, color in ((24, '#DDE9E1'), (10, '#C7DCCF'), (-6, '#AFCDBA')):
            painter.setPen(QPen(QColor('#8FAF9B'), 1))
            painter.setBrush(QColor(color))
            painter.drawRoundedRect(QRectF(-66 + offset, -72, 142, 154), 18, 18)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor('#14452F'), 9))
        painter.drawEllipse(QRectF(-25, -30, 69, 69))
        painter.end()


class StartWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.main_window = None
        self.LoadNotif = None
        self.start_time = time.time()
        self.loader = None
        self.setWindowTitle('DHSYSTEM.SYS')
        self.screen=None

        self.resize(560, 350)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        copy = _SPLASH_COPY[_splash_locale()]

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        panel = QFrame(self)
        panel.setObjectName('splashPanel')
        panel.setStyleSheet('''
            #splashPanel { background: #FFFFFF; border: 1px solid #D5DED8; border-radius: 24px; }
            #splashPanel QLabel { color: #17211C; background: transparent; }
            #splashPanel QLabel#splashEyebrow { color: #14452F; font-size: 11px; font-weight: 700; }
            #splashPanel QLabel#splashBrand { font-size: 34px; font-weight: 700; }
            #splashPanel QLabel#splashDescription { color: #65736B; font-size: 13px; }
            #splashPanel QLabel#splashStatus { color: #496257; font-size: 12px; }
            #splashPanel QProgressBar { border: 0; border-radius: 3px; background: #E7ECE9; height: 5px; }
            #splashPanel QProgressBar::chunk { background: #14452F; border-radius: 3px; }
        ''')
        root.addWidget(panel)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(34, 25, 34, 31)
        layout.setSpacing(8)
        top = QHBoxLayout()
        top.addWidget(QLabel(copy['top']))
        top.addStretch()
        top.addWidget(QLabel(VERSION))
        layout.addLayout(top)
        content = QHBoxLayout()
        text = QVBoxLayout()
        text.addStretch()
        eyebrow = QLabel(copy['eyebrow'])
        eyebrow.setObjectName('splashEyebrow')
        text.addWidget(eyebrow)
        brand = QLabel(copy['brand'])
        brand.setObjectName('splashBrand')
        text.addWidget(brand)
        description = QLabel(copy['title'])
        description.setObjectName('splashDescription')
        description.setWordWrap(True)
        text.addWidget(description)
        text.addStretch()
        content.addLayout(text, 3)
        art = SplashArtwork(panel)
        art.setMinimumSize(170, 190)
        content.addWidget(art, 2)
        layout.addLayout(content, 1)
        self.status_label = QLabel(copy['loading'])
        self.status_label.setObjectName('splashStatus')
        layout.addWidget(self.status_label)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setTextVisible(False)
        layout.addWidget(self.progress)

    def closeEvent(self, event):
        # If main window doesn't exist, quit application
        if self.main_window is None:
            QApplication.instance().quit()

        super().closeEvent(event)

    def update_lable(self, t):
        print(f'{t}')
        copy = _SPLASH_COPY[_splash_locale()]
        if t == 'end':
            self.status_label.setText(copy['ready'])
            QTimer.singleShot(1000, lambda: self.close())
        else:
            self.status_label.setText(copy['loading'])
        QApplication.processEvents()

    def center(self):
        self.screen = QGuiApplication.primaryScreen().geometry()
        if self.screen:
            center_point = self.screen.center()
            self.move(center_point.x() - self.width() // 2, center_point.y() - self.height() // 2)


# Launch main window
def initialize_full_app(start_window, app_instance):
    if sys.stdout is None or sys.stderr is None:
        try:
            log_dir = LOGS_DIR
            os.makedirs(log_dir, exist_ok=True)
            log_file_path = os.path.join(log_dir, f"{time.strftime('%Y%m%d')}.log")
            log_file = open(log_file_path, 'a', encoding='utf-8', buffering=1)
            sys.stdout = log_file
            sys.stderr = log_file
            print(f"\n\n--- Application started at {time.strftime('%Y-%m-%d %H:%M:%S')} ---")
        except Exception as e:
            print(e)

    sys.excepthook = show_global_error_dialog

    start_window.update_lable('Loading resources...')
    # Import qss image resources
    import videotrans.ui.dark.darkstyle_rc
    with open(resource_path('videotrans', 'styles', 'light.qss'), 'r', encoding='utf-8') as f:
        app_instance.setStyleSheet(f.read())
    start_window.update_lable('Loading main window...')

    from videotrans.mainwin.main_win import MainWindow
    try:
        screen = start_window.screen
        w, h = int(screen.width()), int(screen.height())
        sets = QSettings("pyvideotrans", "settings")
        size = sets.value("windowSize", QSize(min(int(w*0.9),1400), min(int(h*0.85),800)))
        start_window.update_lable('Initializing UI...')
        start_window.main_window = MainWindow(width=size.width(), height=size.height(),callback=start_window.update_lable,screen_size=[w,h])
        center_point = screen.center()
        start_window.main_window.move(center_point.x() - size.width() // 2, center_point.y() - size.height() // 2)
    except Exception as e:
        show_global_error_dialog(type(e), e, e.__traceback__)
        app_instance.quit()
        return

def fix_stdio():
    if sys.stdout is None or sys.stderr is None:
        try:
            import ctypes
            if ctypes.windll.kernel32.AttachConsole(-1):
                if sys.stdout is None:
                    sys.stdout = open("CONOUT$", "w", encoding="utf-8", buffering=1)
                if sys.stderr is None:
                    sys.stderr = open("CONOUT$", "w", encoding="utf-8", buffering=1)
                return
        except Exception:
            pass

        if sys.stdout is None:
            sys.stdout = open(os.devnull, "w", encoding="utf-8")
        if sys.stderr is None:
            sys.stderr = open(os.devnull, "w", encoding="utf-8")

def check_and_run_external_script():
    """
    Check if launched as script interpreter.
    Example: sp.exe xxx.py arg1 arg2
    import subprocess
    subprocess.run([sys.executable, r"test.py"])
    import subprocess
    subprocess.run([sys.executable, r"test.py","a","b"])
    """
    if len(sys.argv) > 1 and sys.argv[1].endswith('.py'):
        fix_stdio()  
        import runpy
        script_path = os.path.abspath(sys.argv[1])
        if script_path and os.path.isfile(script_path):
            # Add script_path directory to sys.path to ensure local imports work in script
            script_dir = os.path.dirname(script_path)
            if script_dir not in sys.path:
                sys.path.insert(0, script_dir)

            # Reconstruct sys.argv so external script sees normal sys.argv (sys.argv[0] is script itself)
            sys.argv = sys.argv[1:]

            # Execute external script
            runpy.run_path(script_path, run_name='__main__')
            sys.exit(0)


if __name__ == "__main__":
    check_and_run_external_script()

    # Windows packaging required
    import multiprocessing

    multiprocessing.freeze_support()
    multiprocessing.set_start_method('spawn', force=True)
    qInstallMessageHandler(suppress_qt_warnings)
    atexit.register(cleanup)
    if sys.platform != "win32":
        import signal


        def handle_exit(signum, frame):
            cleanup()
            sys.exit(0)


        signal.signal(signal.SIGINT, handle_exit)
        signal.signal(signal.SIGTERM, handle_exit)

    # Set HighDpi
    try:
        QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    except AttributeError:
        pass

    app = QApplication(sys.argv)
    res = 0
    if getattr(sys, 'frozen', False) and (Path(sys.executable).parent.as_posix()).startswith(
            Path(tempfile.gettempdir()).as_posix()):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setWindowTitle({'vi_VN': 'Lỗi'}.get(_splash_locale(), 'Error'))
        msg_box.setText({
            'vi_VN': 'Hãy giải nén toàn bộ gói rồi mở sp.exe. Không chạy trực tiếp từ tệp nén.',
        }.get(_splash_locale(), 'Extract the complete archive before opening sp.exe.'))
        msg_box.setWindowFlags(msg_box.windowFlags() | Qt.WindowStaysOnTopHint)
        msg_box.exec()
        app.quit()
    else:
        splash = StartWindow()
        splash.setWindowIcon(QIcon(str(resource_path('videotrans', 'styles', 'icon.ico'))))
        splash.center()
        splash.show()

        QTimer.singleShot(100, lambda: initialize_full_app(splash, app))
        try:
            res = app.exec()
            res = 0 if res is None else res
        finally:
            try:
                cleanup()
                #import gc
                #gc.collect()
            except Exception as e:
                print(e)
    sys.exit(res if isinstance(res, int) else 0)
