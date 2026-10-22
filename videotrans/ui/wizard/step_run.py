"""Wizard step 3: start the job, follow each video's stage and review results."""

from pathlib import Path
from typing import Dict, List, Optional

from PySide6.QtCore import QTimer, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from videotrans.configure._i18n import tr

# Stage keys emitted by the task stage methods, grouped into the steps a user sees.
STAGE_GROUPS = (
    ("prepare", ("prepare",)),
    ("recogn", ("recogn",)),
    ("trans", ("trans",)),
    ("dubbing", ("dubbing", "align")),
    ("assemble", ("assemble",)),
)
STAGE_TO_GROUP = {stage: group for group, stages in STAGE_GROUPS for stage in stages}

JOB_WAITING = "waiting"
JOB_RUNNING = "running"
JOB_DONE = "done"
JOB_ERROR = "error"
JOB_STOPPED = "stopped"

JOB_POLL_MS = 50
PURPOSE_TITLE_KEYS = {
    "dub_subtitles": "wizard_purpose_dub",
    "subtitles_only": "wizard_purpose_subtitles",
    "srt_only": "wizard_purpose_srt",
}
JOB_POLL_LIMIT = 100


def parse_percent(text: str) -> Optional[float]:
    """``set_precent`` messages carry ``"<elapsed>???<percent>"``."""
    try:
        return max(0.0, min(100.0, float(str(text).split("???")[1])))
    except (IndexError, ValueError):
        return None


class JobRow(QWidget):
    def __init__(self, uuid: str, name: str, parent=None):
        super().__init__(parent)
        self.uuid = uuid
        self.name = name
        self.state = JOB_WAITING
        self.stage: Optional[str] = None
        self.percent = 0.0
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        top = QHBoxLayout()
        self.title = QLabel(f"<b>{Path(name).name}</b>")
        top.addWidget(self.title, 1)
        self.status = QLabel(tr("wizard_run_waiting"))
        self.status.setObjectName("wizardJobStatus")
        top.addWidget(self.status)
        layout.addLayout(top)
        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setTextVisible(False)
        self.bar.setMaximumHeight(8)
        layout.addWidget(self.bar)
        self.detail = QLabel()
        self.detail.setObjectName("wizardJobDetail")
        self.detail.setStyleSheet("color:#65716b;")
        self.detail.setWordWrap(True)
        layout.addWidget(self.detail)

    def set_stage(self, stage: str):
        group = STAGE_TO_GROUP.get(stage)
        if group is None:
            return
        self.state = JOB_RUNNING
        self.stage = group
        self.status.setText(tr(f"wizard_stage_{group}"))

    def set_percent(self, percent: float):
        self.state = JOB_RUNNING if self.state == JOB_WAITING else self.state
        self.percent = percent
        self.bar.setValue(int(percent))

    def set_detail(self, text: str):
        self.detail.setText(str(text)[:200])

    def finish(self, state: str, text: str = ""):
        self.state = state
        if state == JOB_DONE:
            self.percent = 100.0
            self.bar.setValue(100)
        self.status.setText(tr(f"wizard_run_{state}"))
        self.status.setStyleSheet("color:#b3261e;" if state == JOB_ERROR else "color:#14452f;font-weight:600;")
        if text:
            self.set_detail(text)


class RunStep(QWidget):
    """Owns no processing: it starts and stops through the adapter and listens to task messages."""

    running_changed = Signal(bool)
    translate_another = Signal()

    def __init__(self, adapter, parent=None, *, signal_source=None, purpose=None, open_url=None):
        super().__init__(parent)
        self.setObjectName("wizardRunStep")
        self.adapter = adapter
        self._purpose = purpose or (lambda: "")
        self._open_url = open_url or QDesktopServices.openUrl
        self.rows: Dict[str, JobRow] = {}
        self.receipts: List[dict] = []
        self.running = False
        self._polls = 0
        self._own_videos = set()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        # Everything scrolls so the result panel never forces the window taller than the screen.
        self.scroll = QScrollArea()
        self.scroll.setObjectName("wizardRunScroll")
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        body = QWidget()
        body.setObjectName("wizardRunBody")
        self.scroll.setWidget(body)
        outer.addWidget(self.scroll)
        root = QVBoxLayout(body)
        root.setContentsMargins(0, 0, 8, 0)
        root.setSpacing(12)

        self.ready = QLabel()
        self.ready.setObjectName("wizardRunReady")
        self.ready.setWordWrap(True)
        self.ready.setStyleSheet("font-size:14px;")
        root.addWidget(self.ready)

        top = QHBoxLayout()
        self.overall = QProgressBar()
        self.overall.setObjectName("wizardRunOverall")
        self.overall.setRange(0, 100)
        top.addWidget(self.overall, 1)
        self.stop_button = QPushButton(tr("wizard_run_stop"))
        self.stop_button.setObjectName("wizardRunStop")
        self.stop_button.clicked.connect(self.stop)
        top.addWidget(self.stop_button)
        self.progress_bar_row = QWidget()
        self.progress_bar_row.setLayout(top)
        root.addWidget(self.progress_bar_row)

        self.job_list = QListWidget()
        self.job_list.setObjectName("wizardJobList")
        root.addWidget(self.job_list)

        self.result_holder = QFrame()
        self.result_holder.setObjectName("wizardResultHolder")
        self.result_layout = QVBoxLayout(self.result_holder)
        self.result_layout.setContentsMargins(0, 0, 0, 0)
        self.result_panel = None
        root.addWidget(self.result_holder, 1)
        # Keeps the progress block at the top while no result panel is shown.
        self.spacer = QWidget()
        root.addWidget(self.spacer, 1)

        actions = QHBoxLayout()
        self.folder_button = QPushButton(tr("result_open_folder"))
        self.folder_button.setObjectName("wizardRunOpenFolder")
        self.folder_button.clicked.connect(self.open_folder)
        actions.addWidget(self.folder_button)
        actions.addStretch(1)
        self.again_button = QPushButton(tr("result_translate_another"))
        self.again_button.setObjectName("wizardRunAgain")
        self.again_button.clicked.connect(self._translate_another)
        actions.addWidget(self.again_button)
        root.addLayout(actions)

        if signal_source is None:
            from videotrans.configure.signal_hub import SignalHub
            signal_source = SignalHub.instance()
        signal_source.new_message.connect(self.on_message)
        self.show_ready()

    # ------------------------------------------------------------- states
    def show_ready(self):
        files = self.adapter.videos()
        folder = self.adapter.output_dir() or tr("wizard_output_default")
        purpose = self._purpose()
        lines = [
            f"<b>{tr('wizard_run_ready_title')}</b>",
            f"{tr('wizard_summary_videos')}: {len(files)}",
            f"{tr('wizard_output_dir')} {folder}",
        ]
        if purpose in PURPOSE_TITLE_KEYS:
            lines.insert(1, tr(PURPOSE_TITLE_KEYS[purpose]))
        lines.append(tr("wizard_run_press_start"))
        self.ready.setText("<br>".join(lines))
        self.ready.show()
        self.progress_bar_row.hide()
        self.job_list.hide()
        self.result_holder.hide()
        self.folder_button.hide()
        self.again_button.hide()

    def start(self) -> bool:
        if self.running:
            return False
        self.clear_results()
        if not self.adapter.start_job():
            return False
        self.rows = {}
        self._own_videos = set()
        self.job_list.clear()
        self.ready.hide()
        self.progress_bar_row.show()
        self.stop_button.setEnabled(True)
        self.overall.setValue(0)
        self.job_list.show()
        self._set_running(True)
        self._polls = 0
        self._poll_jobs()
        return True

    def _poll_jobs(self):
        """The classic action builds its job list on a short timer."""
        for uuid, name in self.adapter.jobs():
            self._row(uuid, name)
        if not self.rows and self.running and self._polls < JOB_POLL_LIMIT:
            self._polls += 1
            QTimer.singleShot(JOB_POLL_MS, self._poll_jobs)

    def _row(self, uuid: str, name: str = "") -> JobRow:
        row = self.rows.get(uuid)
        if row is None:
            row = JobRow(uuid, name)
            item = QListWidgetItem()
            item.setSizeHint(row.sizeHint())
            self.job_list.addItem(item)
            self.job_list.setItemWidget(item, row)
            self.rows[uuid] = row
            self._fit_job_list()
        return row

    def _fit_job_list(self, limit: int = 4):
        rows = max(1, min(len(self.rows), limit))
        height = sum(self.job_list.sizeHintForRow(i) for i in range(min(self.job_list.count(), rows)))
        self.job_list.setFixedHeight(max(70, height + 6))

    def stop(self):
        self.adapter.stop_job()
        for row in self.rows.values():
            if row.state in (JOB_WAITING, JOB_RUNNING):
                row.finish(JOB_STOPPED)
        self._finish()

    def _set_running(self, running: bool):
        self.running = running
        self.running_changed.emit(running)

    # ----------------------------------------------------------- messages
    def on_message(self, uuid, message):
        if not self.running or not uuid:
            return
        known = dict(self.adapter.jobs())
        if uuid not in self.rows and uuid not in known:
            return
        row = self._row(uuid, known.get(uuid, ""))
        kind = message["type"]
        text = message["text"]
        if kind == "stage":
            row.set_stage(text)
        elif kind == "set_precent":
            percent = parse_percent(text)
            if percent is not None:
                row.set_percent(percent)
        elif kind == "logs":
            row.set_detail(text)
        elif kind == "succeed":
            row.finish(JOB_DONE)
        elif kind == "error":
            row.finish(JOB_ERROR, text)
        elif kind == "output_receipt":
            self._remember_receipt(text)
            return
        else:
            return
        self._update_overall()

    def _remember_receipt(self, text):
        import json

        try:
            video = json.loads(text).get("video_path")
        except (TypeError, ValueError, AttributeError):
            return
        if video:
            self._own_videos.add(video)

    def _update_overall(self):
        if not self.rows:
            return
        total = sum(row.percent for row in self.rows.values()) / len(self.rows)
        self.overall.setValue(int(total))
        if all(row.state in (JOB_DONE, JOB_ERROR, JOB_STOPPED) for row in self.rows.values()):
            self._finish()

    def _finish(self):
        if not self.running:
            return
        self.stop_button.setEnabled(False)
        self.folder_button.show()
        self.again_button.show()
        self._set_running(False)

    # ------------------------------------------------------------ results
    def owns_results(self, receipts=None) -> bool:
        """Whether these receipts belong to the jobs this page started.

        The classic action clears its job list before it reports results, so the
        page remembers the output videos announced by its own jobs instead.
        """
        if receipts is None:
            return bool(self.rows)
        paths = [item.get("video_path") for item in receipts if isinstance(item, dict)]
        return bool(paths) and all(path in self._own_videos for path in paths)

    def show_results(self, receipts: List[dict], recent: List[dict] = ()):
        from videotrans.ui.result_panel import ResultPanel

        self.receipts = [dict(item) for item in receipts]
        if self.result_panel is None:
            self.result_panel = ResultPanel(self)
            self.result_panel.translate_another.connect(self._translate_another)
            self.result_layout.addWidget(self.result_panel)
        self.result_panel.load_receipts(self.receipts, recent)
        self.result_holder.show()
        self.spacer.hide()
        self._fit_job_list(limit=1)
        self._finish()
        # The result panel has its own folder and "translate another" buttons.
        self.folder_button.hide()
        self.again_button.hide()

    def clear_results(self):
        self.receipts = []
        if self.result_panel is not None:
            self.result_panel.release_media()
        self.result_holder.hide()
        self.spacer.show()

    def open_folder(self):
        folder = self.adapter.output_dir()
        if not folder and self.receipts:
            folder = self.receipts[0].get("target_dir")
        if not folder:
            files = self.adapter.videos()
            if files:
                folder = (Path(files[0]).parent / "_video_out").as_posix()
        if folder and Path(folder).is_dir():
            self._open_url(QUrl.fromLocalFile(folder))

    def reset_run(self):
        """Forget the finished run so the page can prepare a new one."""
        if self.running:
            return
        self.clear_results()
        self.rows = {}
        self._own_videos = set()
        self.job_list.clear()
        self.show_ready()

    def _translate_another(self):
        if self.running:
            return
        self.reset_run()
        self.translate_another.emit()
