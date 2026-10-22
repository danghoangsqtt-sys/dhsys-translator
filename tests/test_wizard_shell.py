import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from types import SimpleNamespace

from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QStackedWidget, QWidget

from videotrans.configure._i18n import tr
from videotrans.ui.wizard import WizardShell
from videotrans.ui.wizard.shell import STEP_OPTIONS, STEP_RUN, STEP_VIDEO

app = QApplication.instance() or QApplication([])


def test_starts_on_first_step_with_back_disabled():
    wizard = WizardShell()

    assert wizard.current_step() == STEP_VIDEO
    assert not wizard.back_button.isEnabled()
    assert wizard.next_button.isEnabled()
    assert wizard.start_button.isHidden()
    assert wizard.step_buttons[0].property("stepState") == "active"
    assert wizard.classic_button.text() == tr("wizard_classic")


def test_next_and_back_walk_the_three_steps():
    wizard = WizardShell()
    wizard.show()
    seen = []
    wizard.step_changed.connect(seen.append)

    assert wizard.next()
    assert wizard.next()
    assert wizard.current_step() == STEP_RUN
    assert wizard.next_button.isHidden()
    assert wizard.start_button.isVisible() and wizard.start_button.isEnabled()
    assert wizard.step_buttons[0].property("stepState") == "done"
    assert wizard.back()
    assert seen == [STEP_OPTIONS, STEP_RUN, STEP_OPTIONS]
    assert wizard.current_step() == STEP_OPTIONS
    assert not wizard.go_to(3)


def test_validator_gates_next_forward_jumps_and_start():
    wizard = WizardShell()
    ready = {"video": False, "options": True}
    wizard.set_step_validator(STEP_VIDEO, lambda: ready["video"])
    wizard.set_step_validator(STEP_OPTIONS, lambda: ready["options"])

    assert not wizard.next_button.isEnabled()
    assert not wizard.go_to(STEP_RUN)
    assert not wizard.step_buttons[STEP_OPTIONS].isEnabled()
    assert wizard.current_step() == STEP_VIDEO

    ready["video"] = True
    wizard.refresh_navigation()
    assert wizard.go_to(STEP_RUN)

    started = []
    wizard.start_requested.connect(lambda: started.append(True))
    ready["options"] = False
    wizard.refresh_navigation()
    assert not wizard.start_button.isEnabled()
    wizard._request_start()
    assert started == []

    ready["options"] = True
    wizard.refresh_navigation()
    wizard.start_button.click()
    assert started == [True]


def test_failing_validator_counts_as_not_ready():
    wizard = WizardShell()
    wizard.set_step_validator(STEP_VIDEO, lambda: 1 / 0)

    assert not wizard.step_ready(STEP_VIDEO)
    assert not wizard.next_button.isEnabled()


def test_backward_jump_is_always_allowed_and_reset_returns_to_start():
    wizard = WizardShell()
    wizard.go_to(STEP_RUN)
    wizard.set_step_validator(STEP_VIDEO, lambda: False)

    assert wizard.go_to(STEP_VIDEO)
    wizard.set_step_validator(STEP_VIDEO, None)
    wizard.go_to(STEP_RUN)
    wizard.reset()
    assert wizard.current_step() == STEP_VIDEO
    assert wizard.step_buttons[STEP_RUN].property("stepState") == "todo"


def test_step_labels_keep_literal_ampersands():
    wizard = WizardShell()

    for button in wizard.step_buttons[1:]:
        assert "&&" in button.text()
        assert "&&" not in tr("wizard_step_options")


def test_classic_button_emits_request():
    wizard = WizardShell()
    requests = []
    wizard.classic_requested.connect(lambda: requests.append(True))

    wizard.classic_button.click()

    assert requests == [True]


def test_set_page_replaces_placeholder_and_keeps_position():
    wizard = WizardShell()
    wizard.go_to(STEP_OPTIONS)
    page = QLabel("real options page")

    wizard.set_page(STEP_OPTIONS, page)

    assert wizard.pages.count() == 3
    assert wizard.pages.widget(STEP_OPTIONS) is page
    assert wizard.pages.currentWidget() is page


class _Params(dict):
    def getset_params(self, update):
        self.update(update)
        return dict(self)


def _router(monkeypatch, mode):
    from videotrans.mainwin import main_win

    saved = _Params(ui_mode=mode)
    monkeypatch.setattr(main_win, "params", saved)
    stack = QStackedWidget()
    home, wizard = QWidget(), QWidget()
    stack.addWidget(home)
    stack.addWidget(wizard)
    hidden = []
    router = SimpleNamespace(page_stack=stack, home_page=home, wizard=wizard,
                             toolBar=SimpleNamespace(hide=lambda: hidden.append(True)))
    router.show_home = lambda: main_win.MainWindow.show_home(router)
    return main_win.MainWindow, router, saved


def test_show_wizard_and_show_classic_switch_pages_and_persist_mode(monkeypatch):
    MainWindow, router, saved = _router(monkeypatch, "classic")

    MainWindow.show_wizard(router)
    assert router.page_stack.currentWidget() is router.wizard
    assert saved["ui_mode"] == "wizard"

    MainWindow.show_classic(router)
    assert router.page_stack.currentWidget() is router.home_page
    assert saved["ui_mode"] == "classic"


def test_classic_workspace_offers_guided_mode(monkeypatch):
    from videotrans.ui import _setup_menus
    from videotrans.ui.en import Ui_MainWindow
    from videotrans.ui.workspace_shell import WorkspaceShell

    monkeypatch.setattr(_setup_menus, "params", _Params(show_all_providers=False))
    opened = []

    class Window(QMainWindow, Ui_MainWindow):
        def show_home(self):
            pass

        def show_wizard(self):
            opened.append(True)

    window = Window()
    window.setupUi(window)
    shell = WorkspaceShell(window, window.takeCentralWidget())

    assert shell.guided_button.isEnabled()
    shell.guided_button.click()
    guided_actions = [a for a in shell.compact_navigation.menu().actions() if a.text() == tr("wizard_open_guided")]
    assert len(guided_actions) == 1
    guided_actions[0].trigger()
    assert opened == [True, True]
