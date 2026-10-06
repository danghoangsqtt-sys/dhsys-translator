"""Read-only, workload-aware system readiness dialog."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from PySide6.QtCore import QObject, QRunnable, QThreadPool, QTimer, Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from videotrans.configure import config
from videotrans.configure._i18n import _get_transobj
from videotrans.diagnostics.remediation import (
    KIND_GUIDANCE,
    KIND_OPEN_URL,
    KIND_WINGET,
    STATUS_GUIDANCE,
    STATUS_LINK_OPENED,
    STATUS_REBOOT_REQUIRED,
    STATUS_SUCCESS,
    execute_remediation,
    get_remediation,
)
from videotrans.diagnostics.system_readiness import (
    ReadinessReport,
    WORKLOAD_BASIC,
    WORKLOAD_CUDA,
    WORKLOAD_LOCAL_MODELS,
    collect_system_readiness,
)


WORKLOAD_ORDER = (WORKLOAD_BASIC, WORKLOAD_LOCAL_MODELS, WORKLOAD_CUDA)
WORKLOAD_LABELS = {
    WORKLOAD_BASIC: "Basic video translation",
    WORKLOAD_LOCAL_MODELS: "Local models",
    WORKLOAD_CUDA: "GPU acceleration",
}
RATING_LABELS = {
    "ready": "Works now",
    "degraded": "Works, but may be slower or limited",
    "blocked": "Needs action",
    "unknown": "Could not fully verify",
}
FINDING_LABELS = {
    "bundle.ffmpeg": "Bundled FFmpeg",
    "bundle.ffprobe": "Bundled ffprobe",
    "bundle.resources": "Application resources",
    "storage.user_data_writable": "User data storage",
    "storage.cache_writable": "Cache storage",
    "memory.ram_gib": "Memory",
    "storage.free_gib": "Free disk space",
    "cpu.logical_count": "CPU threads",
    "gpu.nvidia": "NVIDIA GPU",
    "gpu.cuda_driver": "CUDA driver",
}
ACTION_LABELS = {
    "none": "No action needed",
    "repair_bundle_ffmpeg": "Repair the bundled FFmpeg files",
    "repair_bundle_ffprobe": "Repair the bundled ffprobe files",
    "repair_bundle_resources": "Repair the bundled application resources",
    "fix_user_data_permissions": "Check user-data folder permissions",
    "fix_cache_permissions": "Check cache-folder permissions",
    "close_apps_or_use_lighter_workload": "Close other apps or use a lighter workload",
    "free_disk_space": "Free disk space before processing",
    "expect_slower_processing": "Processing may be slower on this CPU",
    "use_cpu_or_install_nvidia_driver": "Use CPU mode or install/update the NVIDIA driver",
    "install_or_update_nvidia_driver": "Install or update the NVIDIA driver",
    "retry_gpu_detection": "Retry GPU detection after checking the NVIDIA driver",
}


class _TaskSignals(QObject):
    report_ready = Signal(object)
    failed = Signal(str)


class _ReadinessTask(QRunnable):
    def __init__(self, collector: Callable[[], ReadinessReport]):
        super().__init__()
        self.collector = collector
        self.signals = _TaskSignals()

    def run(self):
        try:
            self.signals.report_ready.emit(self.collector())
        except Exception as error:  # UI boundary: keep diagnostics failures recoverable.
            self.signals.failed.emit(str(error))


class Ui_systemcheck(QDialog):
    """Show readiness facts and consent-gated, allowlisted recovery actions."""

    def __init__(
        self,
        *,
        collector=None,
        remediation_executor=None,
        locale: str | None = None,
        auto_refresh: bool = True,
    ):
        super().__init__()
        self._collector = collector or collect_system_readiness
        self._remediation_executor = remediation_executor or self._execute_remediation
        self._catalog = _get_transobj(locale) if locale else None
        self._report: ReadinessReport | None = None
        self._task: _ReadinessTask | None = None
        self._cards: dict[str, tuple[QLabel, QLabel]] = {}
        self._remediation_buttons: dict[str, QPushButton] = {}

        self.setObjectName("systemCheckDialog")
        self.setWindowIcon(QIcon(f"{config.ROOT_DIR}/videotrans/styles/icon.ico"))
        self.setWindowTitle(self._tr("System check"))
        self.resize(760, 680)
        self.setMinimumSize(360, 480)
        self._build_ui()
        if auto_refresh:
            QTimer.singleShot(0, self.refresh_report)

    def _tr(self, key: str, *args) -> str:
        text = self._catalog.get(key, key) if self._catalog is not None else config.tr(key)
        if not args:
            return text
        try:
            return text.format(*args)
        except (IndexError, KeyError):
            return text

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(12)

        title = QLabel(self._tr("Check this PC"), self)
        title.setObjectName("systemCheckTitle")
        title.setStyleSheet("font-size: 24px; font-weight: 700;")
        root.addWidget(title)

        intro = QLabel(self._tr("System check intro"), self)
        intro.setObjectName("systemCheckIntro")
        intro.setWordWrap(True)
        root.addWidget(intro)

        self.scan_state = QLabel(self._tr("Checking this PC..."), self)
        self.scan_state.setObjectName("systemCheckState")
        self.scan_state.setWordWrap(True)
        root.addWidget(self.scan_state)

        scroll = QScrollArea(self)
        scroll.setObjectName("systemCheckScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget(scroll)
        content.setObjectName("systemCheckContent")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(10)

        for workload in WORKLOAD_ORDER:
            card = QFrame(content)
            card.setObjectName(f"readinessCard_{workload}")
            card.setFrameShape(QFrame.Shape.StyledPanel)
            card_layout = QVBoxLayout(card)
            heading = QLabel(self._tr(WORKLOAD_LABELS[workload]), card)
            heading.setStyleSheet("font-size: 16px; font-weight: 700;")
            card_layout.addWidget(heading)
            status = QLabel(self._tr("Could not fully verify"), card)
            status.setObjectName(f"readinessStatus_{workload}")
            status.setWordWrap(True)
            card_layout.addWidget(status)
            details = QLabel(self._tr("Checking this PC..."), card)
            details.setObjectName(f"readinessDetails_{workload}")
            details.setWordWrap(True)
            details.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            card_layout.addWidget(details)
            content_layout.addWidget(card)
            self._cards[workload] = (status, details)

        facts_card = QFrame(content)
        facts_card.setObjectName("systemFactsCard")
        facts_card.setFrameShape(QFrame.Shape.StyledPanel)
        facts_layout = QVBoxLayout(facts_card)
        facts_title = QLabel(self._tr("System facts"), facts_card)
        facts_title.setStyleSheet("font-size: 16px; font-weight: 700;")
        facts_layout.addWidget(facts_title)
        self.system_facts = QLabel(self._tr("Checking this PC..."), facts_card)
        self.system_facts.setObjectName("systemFacts")
        self.system_facts.setWordWrap(True)
        self.system_facts.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        facts_layout.addWidget(self.system_facts)
        content_layout.addWidget(facts_card)

        remediation_card = QFrame(content)
        remediation_card.setObjectName("systemRemediationCard")
        remediation_card.setFrameShape(QFrame.Shape.StyledPanel)
        remediation_layout = QVBoxLayout(remediation_card)
        remediation_title = QLabel(self._tr("Recommended fixes"), remediation_card)
        remediation_title.setStyleSheet("font-size: 16px; font-weight: 700;")
        remediation_layout.addWidget(remediation_title)
        remediation_intro = QLabel(self._tr("Remediation consent intro"), remediation_card)
        remediation_intro.setWordWrap(True)
        remediation_layout.addWidget(remediation_intro)
        self.remediation_actions = QWidget(remediation_card)
        self.remediation_actions_layout = QVBoxLayout(self.remediation_actions)
        self.remediation_actions_layout.setContentsMargins(0, 0, 0, 0)
        self.remediation_actions_layout.setSpacing(6)
        remediation_layout.addWidget(self.remediation_actions)
        self.remediation_empty = QLabel(self._tr("No allowlisted fix is needed."), remediation_card)
        self.remediation_empty.setWordWrap(True)
        remediation_layout.addWidget(self.remediation_empty)
        content_layout.addWidget(remediation_card)
        content_layout.addStretch()
        scroll.setWidget(content)
        root.addWidget(scroll, 1)

        buttons = QVBoxLayout()
        self.refresh_button = QPushButton(self._tr("Refresh"), self)
        self.refresh_button.setObjectName("systemCheckRefresh")
        self.copy_button = QPushButton(self._tr("Copy support report"), self)
        self.copy_button.setObjectName("systemCheckCopy")
        self.export_button = QPushButton(self._tr("Export support report"), self)
        self.export_button.setObjectName("systemCheckExport")
        self.close_button = QPushButton(self._tr("Close"), self)
        self.close_button.setObjectName("systemCheckClose")
        for button in (self.refresh_button, self.copy_button, self.export_button, self.close_button):
            button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            buttons.addWidget(button)
        root.addLayout(buttons)

        self.refresh_button.clicked.connect(self.refresh_report)
        self.copy_button.clicked.connect(self.copy_report)
        self.export_button.clicked.connect(self.export_report)
        self.close_button.clicked.connect(self.close)
        self.copy_button.setEnabled(False)
        self.export_button.setEnabled(False)
        QWidget.setTabOrder(self.refresh_button, self.copy_button)
        QWidget.setTabOrder(self.copy_button, self.export_button)
        QWidget.setTabOrder(self.export_button, self.close_button)

    def refresh_report(self):
        if self._task is not None:
            return
        self.scan_state.setText(self._tr("Checking this PC..."))
        self.refresh_button.setEnabled(False)
        task = _ReadinessTask(self._collector)
        self._task = task
        task.signals.report_ready.connect(self._finish_refresh)
        task.signals.failed.connect(self._fail_refresh)
        QThreadPool.globalInstance().start(task)

    def _finish_refresh(self, report):
        self._task = None
        self.refresh_button.setEnabled(True)
        self.set_report(report)

    def _fail_refresh(self, message: str):
        self._task = None
        self.refresh_button.setEnabled(True)
        self.scan_state.setText(self._tr("Could not complete system check: {}", message))

    def set_report(self, report: ReadinessReport):
        """Render an already-sanitized report; useful for deterministic UI tests."""

        self._report = report
        self.copy_button.setEnabled(True)
        self.export_button.setEnabled(True)
        self.scan_state.setText(self._tr("System check is read-only and finished."))
        finding_by_code = {finding.code: finding for finding in report.findings}

        for workload in WORKLOAD_ORDER:
            rating = report.workloads[workload]
            status, details = self._cards[workload]
            status.setText(self._tr(RATING_LABELS.get(rating.rating, "Could not fully verify")))
            issue_codes = list(rating.blocking_codes)
            issue_codes.extend(code for code in rating.advisory_codes if code not in issue_codes)
            issue_codes.extend(code for code in rating.unknown_codes if code not in issue_codes)
            if not issue_codes:
                details.setText(self._tr("No action needed for this workload."))
                continue
            lines = []
            for code in issue_codes:
                finding = finding_by_code.get(code)
                if finding is None:
                    continue
                label = self._tr(FINDING_LABELS.get(code, code))
                action = self._tr(ACTION_LABELS.get(finding.action_code, finding.action_code))
                lines.append(f"{label}: {action}")
            details.setText("\n".join(lines) or self._tr("Could not fully verify"))

        self.system_facts.setText(self._system_summary(report, finding_by_code))
        self._render_remediation_actions(report)

    def _render_remediation_actions(self, report: ReadinessReport):
        while self.remediation_actions_layout.count():
            item = self.remediation_actions_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._remediation_buttons.clear()

        action_codes = []
        for finding in report.findings:
            code = finding.action_code
            if code == "none" or code in action_codes or get_remediation(code) is None:
                continue
            action_codes.append(code)

        self.remediation_empty.setVisible(not action_codes)
        for code in action_codes:
            action = get_remediation(code)
            if action is None:
                continue
            button = QPushButton(self._tr(action.title), self.remediation_actions)
            button.setObjectName(f"remediation_{code}")
            button.setToolTip(self._tr(action.description))
            button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            button.clicked.connect(lambda _checked=False, action_code=code: self._request_remediation(action_code))
            self.remediation_actions_layout.addWidget(button)
            self._remediation_buttons[code] = button

    def _confirmation_text(self, action_code: str) -> str:
        action = get_remediation(action_code)
        if action is None:
            return self._tr("This remediation is not in the verified allowlist.")
        if action.kind == KIND_WINGET:
            exact_target = action.package_id or self._tr("Unknown")
        elif action.kind == KIND_OPEN_URL:
            exact_target = action.official_url or self._tr("Unknown")
        else:
            exact_target = self._tr("Guidance only; no installer will run")
        return "\n".join((
            f"{self._tr('Action')}: {self._tr(action.title)}",
            f"{self._tr('Publisher')}: {action.publisher}",
            f"{self._tr('Source')}: {self._tr(action.source)}",
            f"{self._tr('Exact target')}: {exact_target}",
            f"{self._tr('May request Windows elevation')}: {self._tr('Yes') if action.requires_elevation else self._tr('No')}",
            f"{self._tr('May require restart')}: {self._tr('Yes') if action.restart_possible else self._tr('No')}",
            "",
            self._tr(action.description),
        ))

    def _request_remediation(self, action_code: str):
        action = get_remediation(action_code)
        if action is None:
            QMessageBox.warning(
                self,
                self._tr("Action blocked"),
                self._tr("This remediation is not in the verified allowlist."),
            )
            return None

        reply = QMessageBox.question(
            self,
            self._tr("Confirm action"),
            self._confirmation_text(action_code),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            self.scan_state.setText(self._tr("Cancelled. No system change was made."))
            return None

        result = self._remediation_executor(action_code, confirmed=True)
        message = self._result_message(result.status, action.description)
        self.scan_state.setText(message)
        if result.status in (STATUS_GUIDANCE, STATUS_LINK_OPENED, STATUS_SUCCESS, STATUS_REBOOT_REQUIRED):
            QMessageBox.information(self, self._tr("Action result"), message)
        else:
            QMessageBox.warning(self, self._tr("Action result"), message)
        if result.status == STATUS_SUCCESS:
            QTimer.singleShot(0, self.refresh_report)
        return result

    def _execute_remediation(self, action_code: str, *, confirmed: bool):
        return execute_remediation(
            action_code,
            confirmed=confirmed,
            url_opener=lambda url: bool(QDesktopServices.openUrl(QUrl(url))),
        )

    def _result_message(self, status: str, guidance: str) -> str:
        messages = {
            STATUS_GUIDANCE: self._tr(guidance),
            STATUS_LINK_OPENED: self._tr("Opened the verified official page. Complete the action there, then run System check again."),
            STATUS_SUCCESS: self._tr("The prerequisite was installed and verified. System check will run again."),
            STATUS_REBOOT_REQUIRED: self._tr("Windows must restart before this prerequisite can be verified."),
            "cancelled": self._tr("Cancelled. No system change was made."),
            "missing_winget": self._tr("WinGet is not available. Use the verified official manual recovery path."),
            "unavailable": self._tr("The verified recovery action is unavailable. Check the network connection and try again."),
            "uac_denied": self._tr("Windows elevation was cancelled or denied. No other installer will run automatically."),
            "installer_failed": self._tr("The installer failed. No other package will be attempted automatically."),
            "post_check_failed": self._tr("The installer finished, but the prerequisite is still not verified. Restart if requested, then scan again."),
            "not_allowed": self._tr("This remediation is not in the verified allowlist."),
        }
        return messages.get(status, self._tr("Could not complete the recovery action."))

    def _system_summary(self, report: ReadinessReport, finding_by_code) -> str:
        system = report.system
        lines = [
            f"{self._tr('OS')}: {system.get('os', 'unknown')} {system.get('os_release', '')}".strip(),
            f"{self._tr('Architecture')}: {system.get('architecture', 'unknown')}",
        ]
        for code in ("cpu.logical_count", "memory.ram_gib", "storage.free_gib", "gpu.nvidia", "gpu.cuda_driver"):
            finding = finding_by_code.get(code)
            if finding is None:
                continue
            lines.append(f"{self._tr(FINDING_LABELS[code])}: {self._format_value(code, finding.value)}")
        return "\n".join(lines)

    def _format_value(self, code: str, value) -> str:
        if value is None:
            return self._tr("Unknown")
        if code == "memory.ram_gib" or code == "storage.free_gib":
            return f"{value} GiB"
        if code == "gpu.nvidia" and isinstance(value, dict):
            count = value.get("count", 0)
            vram = value.get("vram_mib")
            return f"{count} GPU" + (f", {vram} MiB VRAM" if vram else "")
        return str(value)

    def report_text(self) -> str | None:
        if self._report is None:
            return None
        return json.dumps(self._report.to_dict(), ensure_ascii=False, indent=2)

    def copy_report(self):
        payload = self.report_text()
        if payload is None:
            return False
        QApplication.clipboard().setText(payload)
        self.scan_state.setText(self._tr("Support report copied."))
        return True

    def export_report(self, path: str | Path | None = None):
        payload = self.report_text()
        if payload is None:
            return None
        if path is None or isinstance(path, bool):
            selected, _ = QFileDialog.getSaveFileName(
                self,
                self._tr("Export support report"),
                "pyvideotrans-system-report.json",
                "JSON (*.json)",
            )
            if not selected:
                return None
            path = selected
        target = Path(path)
        target.write_text(payload + "\n", encoding="utf-8")
        self.scan_state.setText(self._tr("Support report exported."))
        return target
