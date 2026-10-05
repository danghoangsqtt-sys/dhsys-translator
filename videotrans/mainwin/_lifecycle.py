import os
import shutil
import subprocess
import sys
from pathlib import Path

import psutil


class LifecycleMixin:

    def restart_app(self):
        from PySide6.QtWidgets import QMessageBox
        from videotrans.configure.config import tr

        reply = QMessageBox.question(
            self,
            tr("Restart"),
            tr("Are you sure you want to restart the application?"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.is_restarting = True
            self.close()

    @staticmethod
    def kill_ffmpeg_processes():
        from videotrans.configure.config import logger
        owned = []
        try:
            for child in psutil.Process().children(recursive=True):
                try:
                    if child.name().lower() in ('ffmpeg', 'ffmpeg.exe'):
                        owned.append(child)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            for child in owned:
                try:
                    child.terminate()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            _, alive = psutil.wait_procs(owned, timeout=3)
            for child in alive:
                try:
                    child.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except (psutil.NoSuchProcess, psutil.AccessDenied) as exc:
            logger.warning(f'Could not inspect FFmpeg child processes: {exc}')

    def closeEvent(self, event):
        self.hide()
        from videotrans.configure.config import app_cfg, ROOT_DIR, TEMP_DIR, TEMP_ROOT,REDUBB_STATUS_FILE
        try:
            if Path(REDUBB_STATUS_FILE).exists():
                Path(REDUBB_STATUS_FILE).write_text('end')
        except OSError:
            pass
        app_cfg.exit_soft = True
        app_cfg.current_status = 'stop'
        os.chdir(ROOT_DIR)
        self.cleanup_and_accept()

        try:
            shutil.rmtree(TEMP_DIR, ignore_errors=True)
        except OSError:
            pass
        # 清理 TEMP_ROOT 下的 txt srt json 文件，
        # 不直接删除 tmp 文件夹，避免同时启动多个实例导致其他报错，保留 pid 状态文件，防止其他实例出错
        for it in Path(TEMP_ROOT).iterdir():
            if it.is_file() and it.suffix.lower()!='pid':
                try:
                    it.unlink()
                except Exception:
                    pass

        if not self.is_restarting:
            event.accept()
            return

        args = sys.argv[1:]
        locale = getattr(self, '_restart_locale', None)
        if locale:
            clean_args = []
            skip_next = False
            for arg in args:
                if skip_next:
                    skip_next = False
                elif arg == '--lang':
                    skip_next = True
                elif not arg.startswith('--lang='):
                    clean_args.append(arg)
            args = clean_args + ['--lang', locale]
        if getattr(sys, 'frozen', False):
            subprocess.Popen([sys.executable] + args)
        else:
            subprocess.Popen([sys.executable, sys.argv[0]] + args)

        event.accept()
        os._exit(0)

    def cleanup_and_accept(self):
        from PySide6.QtCore import QCoreApplication, QSettings, QThreadPool
        from videotrans.configure.config import app_cfg, logger

        QCoreApplication.processEvents()
        sets = QSettings("pyvideotrans", "settings")
        sets.setValue("windowSize", self.size())
        try:
            for w in app_cfg.child_forms.values():
                if w and hasattr(w, 'hide'):
                    w.hide()
        except Exception as e:
            logger.exception(f'Sub-window hiding process failed {e}', exc_info=True)

        for thread in self.worker_threads:
            if thread and thread.isRunning():
                thread.requestInterruption()

        # 等待所有线程安全结束
        for thread in self.worker_threads:
            if thread and thread.isRunning():
                thread.wait(3000)  # 等待3秒

        try:
            for w in app_cfg.child_forms.values():
                if w and hasattr(w, 'close'):
                    w.close()
        except Exception as e:
            logger.exception(f'Sub-window closing process failed{e}', exc_info=True)

        QThreadPool.globalInstance().waitForDone(5000)
        self.kill_ffmpeg_processes()
