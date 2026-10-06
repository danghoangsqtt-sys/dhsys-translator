"""Read-only, workload-aware system readiness dialog."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from PySide6.QtCore import QObject, QRunnable, QThreadPool, QTimer, Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from videotrans.configure import config
from videotrans.configure._i18n import _get_transobj
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
    """Show sanitized readiness facts without changing the machine."""

    def __init__(self, *, collector=None, locale: str | None = None, auto_refresh: bool = True):
        super().__init__()
        self._collector = collector or collect_system_readiness
        self._catalog = _get_transobj(locale) if locale else None
        self._report: ReadinessReport | None = None
        self._task: _ReadinessTask | None = None
        self._cards: dict[str, tuple[QLabel, QLabel]] = {}

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
