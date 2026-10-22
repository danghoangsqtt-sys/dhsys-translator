import json
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from types import SimpleNamespace

from PySide6.QtCore import QObject, QUrl, Signal
from PySide6.QtWidgets import QApplication

from videotrans.configure._i18n import tr
from videotrans.task.taskcfg import SignMsg
from videotrans.ui.wizard.step_run import JOB_DONE, JOB_ERROR, JOB_STOPPED, RunStep, parse_percent

app = QApplication.instance() or QApplication([])


class Hub(QObject):
    new_message = Signal(str, object)

    def send(self, uuid, kind, text=""):
        self.new_message.emit(uuid, SignMsg(type=kind, uuid=uuid, text=text))


class FakeAdapter:
    def __init__(self, files=("D:/a.mp4",), start_ok=True):
        self.files = list(files)
        self.start_ok = start_ok
        self.running = False
        self.job_list = []
        self.stopped = 0
        self.out = None

    def videos(self):
        return list(self.files)

    def output_dir(self):
        return self.out

    def start_job(self):
        if not self.start_ok:
            return False
        self.running = True
        self.job_list = [(f"u{i}", path) for i, path in enumerate(self.files)]
        return True

    def stop_job(self):
        self.stopped += 1
        self.running = False

    def jobs(self):
        return list(self.job_list)


def _page(adapter=None, **kwargs):
    hub = Hub()
    adapter = adapter or FakeAdapter()
    page = RunStep(adapter, signal_source=hub, purpose=lambda: "dub_subtitles", **kwargs)
    return page, adapter, hub


def test_parse_percent():
    assert parse_percent("12???37.5") == 37.5
    assert parse_percent("1???140") == 100.0
    assert parse_percent("bad") is None


def test_ready_state_before_start():
    page, _, _ = _page()

    assert not page.ready.isHidden()
    assert tr("wizard_run_ready_title") in page.ready.text()
    assert tr("wizard_purpose_dub") in page.ready.text()
    assert page.job_list.isHidden()
    assert page.again_button.isHidden()


def test_failed_start_keeps_ready_state():
    page, adapter, _ = _page(FakeAdapter(start_ok=False))
    states = []
    page.running_changed.connect(states.append)

    assert page.start() is False
    assert not page.running
    assert states == []
    assert not page.ready.isHidden()


def test_single_job_follows_stages_progress_and_finishes():
    page, adapter, hub = _page()
    states = []
    page.running_changed.connect(states.append)

    assert page.start()
    assert states == [True]
    assert list(page.rows) == ["u0"]
    row = page.rows["u0"]

    hub.send("u0", "stage", "recogn")
    assert row.status.text() == tr("wizard_stage_recogn")
    hub.send("u0", "set_precent", "5???42")
    assert row.bar.value() == 42 and page.overall.value() == 42
    hub.send("u0", "logs", "Đang nhận dạng 3/10")
    assert "3/10" in row.detail.text()
    hub.send("u0", "stage", "align")
    assert row.status.text() == tr("wizard_stage_dubbing")
    hub.send("other", "stage", "trans")
    assert list(page.rows) == ["u0"]

    hub.send("u0", "succeed", "D:/a.mp4")
    assert row.state == JOB_DONE
    assert page.overall.value() == 100
    assert states == [True, False]
    assert not page.again_button.isHidden()
    assert not page.stop_button.isEnabled()


def test_batch_reports_each_video_and_errors():
    page, adapter, hub = _page(FakeAdapter(files=["D:/a.mp4", "D:/b.mp4"]))
    page.start()

    hub.send("u0", "succeed")
    assert page.running
    hub.send("u1", "error", "Network down")
    assert page.rows["u1"].state == JOB_ERROR
    assert "Network down" in page.rows["u1"].detail.text()
    assert not page.running


def test_stop_uses_adapter_and_marks_unfinished_jobs():
    page, adapter, hub = _page(FakeAdapter(files=["D:/a.mp4", "D:/b.mp4"]))
    page.start()
    hub.send("u0", "succeed")

    page.stop()

    assert adapter.stopped == 1
    assert page.rows["u0"].state == JOB_DONE
    assert page.rows["u1"].state == JOB_STOPPED
    assert not page.running


def test_messages_are_ignored_when_not_running():
    page, adapter, hub = _page()
    hub.send("u0", "stage", "recogn")
    assert page.rows == {}


def test_results_embed_panel_only_for_own_jobs(tmp_path):
    video = tmp_path / "clip-vi.mp4"
    video.write_bytes(b"0" * 10)
    page, adapter, hub = _page()
    page.start()
    receipt = {"video_path": str(video), "subtitle_type": 1, "target_dir": str(tmp_path)}
    hub.send("u0", "output_receipt", json.dumps(receipt))
    hub.send("u0", "succeed")
    adapter.job_list = []  # the classic action resets its job list before reporting

    assert page.owns_results([receipt])
    assert not page.owns_results([{"video_path": "D:/classic-job.mp4"}])
    assert not page.owns_results([])
    page.show_results([receipt])
    assert page.result_panel is not None
    assert not page.result_holder.isHidden()
    assert page.result_panel.title.text() == "clip-vi.mp4"


def test_translate_another_clears_and_emits(tmp_path):
    page, adapter, hub = _page()
    requests = []
    page.translate_another.connect(lambda: requests.append(True))
    page.start()
    page._translate_another()
    assert requests == []

    hub.send("u0", "succeed")
    page.again_button.click()
    assert requests == [True]
    assert page.rows == {}


def test_open_folder_prefers_output_dir(tmp_path):
    opened = []
    adapter = FakeAdapter(files=[str(tmp_path / "a.mp4")])
    adapter.out = str(tmp_path)
    page, _, _ = _page(adapter, open_url=opened.append)

    page.open_folder()
    assert opened == [QUrl.fromLocalFile(str(tmp_path))]


def test_shell_busy_lock_blocks_navigation():
    from videotrans.ui.wizard import WizardShell
    from videotrans.ui.wizard.shell import STEP_RUN

    wizard = WizardShell()
    wizard.go_to(STEP_RUN)
    wizard.set_busy(True)

    assert not wizard.back_button.isEnabled()
    assert not wizard.classic_button.isEnabled()
    assert wizard.start_button.isHidden()
    assert not wizard.go_to(0)
    wizard.set_busy(False)
    assert wizard.go_to(0)


def test_result_routing_prefers_wizard_when_it_owns_the_job(monkeypatch, tmp_path):
    from videotrans.mainwin._actions_task import WinActionTaskMixin
    from videotrans.ui import result_history

    monkeypatch.setattr(result_history, "default_history_path", lambda: tmp_path / "h.json")
    shown = []
    run = SimpleNamespace(owns_results=lambda receipts=None: True, show_results=lambda receipts, recent: shown.append(receipts))
    action = SimpleNamespace(main=SimpleNamespace(wizard_run=run), result_dialog=None)
    receipts = [{"video_path": str(tmp_path / "v.mp4")}]

    assert WinActionTaskMixin.show_result_dialog(action, receipts) is run
    assert shown == [receipts]
    assert result_history.load_history(tmp_path / "h.json")[0]["video_path"].endswith("v.mp4")


def test_start_is_withheld_after_a_finished_job_until_reset():
    from videotrans.ui.wizard import WizardShell
    from videotrans.ui.wizard.shell import STEP_RUN

    wizard = WizardShell()
    wizard.go_to(STEP_RUN)
    started = []
    wizard.start_requested.connect(lambda: started.append(True))

    wizard.set_start_allowed(False)
    assert wizard.start_button.isHidden()
    wizard._request_start()
    assert started == []

    wizard.set_start_allowed(True)
    wizard.start_button.click()
    assert started == [True]


def test_reset_run_returns_to_ready_state(tmp_path):
    video = tmp_path / "v.mp4"
    video.write_bytes(b"0")
    page, adapter, hub = _page()
    page.start()
    receipt = {"video_path": str(video)}
    hub.send("u0", "output_receipt", json.dumps(receipt))
    hub.send("u0", "succeed")
    page.show_results([receipt])
    assert page.again_button.isHidden()

    page.reset_run()

    assert page.rows == {}
    assert not page.owns_results([receipt])
    assert not page.ready.isHidden()
    assert page.result_holder.isHidden()


def test_result_buttons_keep_literal_ampersand():
    from videotrans.ui.result_panel import ResultPanel

    panel = ResultPanel()
    assert "&&" in panel.reexport_button.text()
