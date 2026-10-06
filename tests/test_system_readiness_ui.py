import json

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from PySide6.QtWidgets import QMessageBox

from videotrans.diagnostics.remediation import RemediationResult, STATUS_GUIDANCE
from videotrans.diagnostics.system_readiness import (
    GIB,
    NvidiaProbe,
    ProbeSnapshot,
    STATUS_WARNING,
    evaluate_readiness,
)
from videotrans.ui import systemcheck
from videotrans.ui.systemcheck import Ui_systemcheck


app = QApplication.instance() or QApplication([])


def _report(*, cpu_only=False, low_disk=False, missing_ffmpeg=False):
    return evaluate_readiness(ProbeSnapshot(
        os_name="Windows",
        os_release="11",
        architecture="AMD64",
        cpu_logical_count=12,
        ram_bytes=16 * GIB,
        disk_free_bytes=(2 if low_disk else 64) * GIB,
        ffmpeg_present=not missing_ffmpeg,
        ffprobe_present=True,
        resources_present=True,
        user_data_writable=True,
        cache_writable=True,
        nvidia=(
            NvidiaProbe(state=STATUS_WARNING, gpu_count=0, total_vram_mib=0)
            if cpu_only else
            NvidiaProbe(state="ok", gpu_count=1, total_vram_mib=8192, cuda_driver_version="12.8")
        ),
    ))


def test_vietnamese_and_english_copy_explains_workload_outcomes():
    report = _report(cpu_only=True)

    vi = Ui_systemcheck(locale="vi_VN", auto_refresh=False)
    vi.set_report(report)
    assert vi.windowTitle() == "Kiểm tra máy"
    assert vi._cards["basic"][0].text() == "Có thể dùng ngay"
    assert "chậm" in vi._cards["local_models"][0].text().lower()
    assert "Cần xử lý" in vi._cards["cuda_acceleration"][0].text()
    assert "Không phát hiện NVIDIA GPU khả dụng" not in vi._cards["cuda_acceleration"][1].text()

    en = Ui_systemcheck(locale="en_US", auto_refresh=False)
    en.set_report(report)
    assert en.windowTitle() == "System check"
    assert en._cards["basic"][0].text() == "Works now"
    assert en._cards["local_models"][0].text() == "Works, but may be slower or limited"
    assert en._cards["cuda_acceleration"][0].text() == "Needs action"
    assert "Không" not in en._cards["cuda_acceleration"][1].text()


def test_report_copy_and_export_use_only_sanitized_payload(tmp_path):
    private_path = tmp_path / "Alice" / "secret-video.mp4"
    dialog = Ui_systemcheck(locale="en_US", auto_refresh=False)
    dialog.set_report(_report())

    assert dialog.copy_report() is True
    copied = QApplication.clipboard().text()
    exported = tmp_path / "support.json"
    assert dialog.export_report(exported) == exported
    saved = exported.read_text(encoding="utf-8")

    assert json.loads(copied) == json.loads(saved)
    assert str(private_path) not in copied
    assert "secret-video.mp4" not in copied
    assert "api_key" not in copied.lower()
    assert "token" not in copied.lower()


def test_refresh_runs_in_worker_boundary_and_does_not_modify_machine(monkeypatch):
    calls = []

    class ImmediatePool:
        @staticmethod
        def start(task):
            task.run()

    class ImmediateThreadPool:
        @staticmethod
        def globalInstance():
            return ImmediatePool()

    monkeypatch.setattr(systemcheck, "QThreadPool", ImmediateThreadPool)
    dialog = Ui_systemcheck(
        locale="en_US",
        collector=lambda: calls.append("scan") or _report(low_disk=True),
        auto_refresh=False,
    )

    dialog.refresh_report()

    assert calls == ["scan"]
    assert dialog._report is not None
    assert dialog._cards["basic"][0].text() == "Needs action"
    assert dialog.refresh_button.isEnabled()


def test_narrow_window_keyboard_navigation_and_no_auto_close():
    dialog = Ui_systemcheck(locale="vi_VN", auto_refresh=False)
    dialog.set_report(_report(cpu_only=True))
    dialog.resize(380, 620)
    dialog.show()
    app.processEvents()

    assert dialog.width() <= 400
    assert dialog.findChild(type(dialog.scan_state), "systemCheckIntro").wordWrap()
    assert dialog.isVisible()

    dialog.refresh_button.setFocus()
    app.processEvents()
    QTest.keyClick(dialog.refresh_button, Qt.Key.Key_Tab)
    app.processEvents()
    assert dialog.focusWidget() is dialog.copy_button
    QTest.keyClick(dialog.copy_button, Qt.Key.Key_Tab)
    app.processEvents()
    assert dialog.focusWidget() is dialog.export_button

    QTest.qWait(30)
    app.processEvents()
    assert dialog.isVisible()
    dialog.close()


def test_generated_workspace_reuses_systemcheck_action_in_sidebar_and_compact_menu():
    from PySide6.QtWidgets import QMainWindow
    from videotrans.ui.en import Ui_MainWindow
    from videotrans.ui.workspace_shell import WorkspaceShell

    class GeneratedWindow(QMainWindow, Ui_MainWindow):
        def show_home(self):
            pass

    window = GeneratedWindow()
    window.setupUi(window)
    shell = WorkspaceShell(window, window.takeCentralWidget())

    assert shell.system_check.defaultAction() is window.systemcheck
    assert window.systemcheck in shell.compact_navigation.menu().actions()
    assert window.systemcheck in {
        action for section in shell._catalog_sections for action in section.actions()
    }


def test_remediation_cancel_requires_confirmation_and_has_no_effect(monkeypatch):
    calls = []
    dialog = Ui_systemcheck(
        locale="en_US",
        auto_refresh=False,
        remediation_executor=lambda code, confirmed: calls.append((code, confirmed)),
    )
    dialog.set_report(_report(missing_ffmpeg=True))
    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *args, **kwargs: QMessageBox.StandardButton.No,
    )

    dialog._remediation_buttons["repair_bundle_ffmpeg"].click()

    assert calls == []
    assert dialog.scan_state.text() == "Cancelled. No system change was made."


def test_gpu_recovery_confirmation_shows_verified_source_and_url(monkeypatch):
    prompts = []
    dialog = Ui_systemcheck(locale="en_US", auto_refresh=False)
    dialog.set_report(_report(cpu_only=True))

    def cancel(*args, **kwargs):
        prompts.append(args[2])
        return QMessageBox.StandardButton.No

    monkeypatch.setattr(QMessageBox, "question", cancel)
    dialog._remediation_buttons["use_cpu_or_install_nvidia_driver"].click()

    assert len(prompts) == 1
    assert "NVIDIA" in prompts[0]
    assert "https://www.nvidia.com/Download/index.aspx" in prompts[0]
    assert "Exact target" in prompts[0]


def test_confirmed_guidance_runs_exact_action_without_silent_installer(monkeypatch):
    calls = []
    messages = []

    def executor(code, confirmed):
        calls.append((code, confirmed))
        return RemediationResult(
            action_code=code,
            status=STATUS_GUIDANCE,
            method="guidance",
            message="fixed guidance",
        )

    dialog = Ui_systemcheck(
        locale="en_US",
        auto_refresh=False,
        remediation_executor=executor,
    )
    dialog.set_report(_report(missing_ffmpeg=True))
    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
    )
    monkeypatch.setattr(
        QMessageBox,
        "information",
        lambda *args, **kwargs: messages.append(args[2]) or QMessageBox.StandardButton.Ok,
    )

    dialog._remediation_buttons["repair_bundle_ffmpeg"].click()

    assert calls == [("repair_bundle_ffmpeg", True)]
    assert messages
    assert "FFmpeg is bundled" in messages[0]
