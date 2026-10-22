"""Container and step navigation for the guided wizard.

The shell is presentation only: pages are plain widgets supplied by later tasks,
and each step's readiness comes from a validator callable.  It never reads or
writes params and never starts media processing itself; it emits signals.
"""

from typing import Callable, Dict, List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from videotrans.configure._i18n import tr

STEP_VIDEO = 0
STEP_OPTIONS = 1
STEP_RUN = 2

STEP_TITLE_KEYS = ("wizard_step_video", "wizard_step_options", "wizard_step_run")
STEP_HINT_KEYS = ("wizard_hint_video", "wizard_hint_options", "wizard_hint_run")

# Colours follow the light workspace tokens (.DHSYSTEM/ui-direction design_tokens).
STEPPER_STYLE = """
QPushButton#wizardStep { border: 1px solid #d9e0dc; border-radius: 16px; padding: 6px 14px;
    background: #f4f6f5; color: #65716b; }
QPushButton#wizardStep[stepState="active"] { background: #14452f; color: #ffffff; border-color: #14452f; font-weight: 600; }
QPushButton#wizardStep[stepState="done"] { background: #dcede4; color: #14452f; border-color: #dcede4; }
QPushButton#wizardStep:focus { border: 2px solid #2f7956; }
"""


class WizardShell(QWidget):
    """Stepper header, one page per step and a Back/Next/Start footer."""

    classic_requested = Signal()
    start_requested = Signal()
    step_changed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("wizardShell")
        self._validators: Dict[int, Callable[[], bool]] = {}
        self._visited = {STEP_VIDEO}
        self._current = STEP_VIDEO
        self._busy = False
        self._start_allowed = True

        root = QVBoxLayout(self)
        root.setContentsMargins(22, 18, 22, 18)
        root.setSpacing(14)

        header = QHBoxLayout()
        brand = QLabel("DHSYSTEM.SYS")
        brand.setObjectName("wizardBrand")
        header.addWidget(brand)
        header.addStretch(1)
        self.classic_button = QPushButton(tr("wizard_classic"))
        self.classic_button.setObjectName("wizardClassic")
        self.classic_button.setToolTip(tr("wizard_classic_tip"))
        self.classic_button.clicked.connect(self.classic_requested)
        header.addWidget(self.classic_button)
        root.addLayout(header)

        stepper = QFrame()
        stepper.setObjectName("wizardStepper")
        stepper.setStyleSheet(STEPPER_STYLE)
        stepper_layout = QHBoxLayout(stepper)
        stepper_layout.setContentsMargins(0, 0, 0, 0)
        stepper_layout.setSpacing(8)
        self.step_buttons: List[QPushButton] = []
        for index, key in enumerate(STEP_TITLE_KEYS):
            # "&&" keeps a literal ampersand instead of a keyboard mnemonic.
            button = QPushButton(f"{index + 1}  {tr(key)}".replace("&", "&&"))
            button.setObjectName("wizardStep")
            button.setCheckable(True)
            button.setAccessibleName(tr(key))
            button.clicked.connect(lambda _checked=False, step=index: self.go_to(step))
            self.step_buttons.append(button)
            stepper_layout.addWidget(button)
        stepper_layout.addStretch(1)
        root.addWidget(stepper)

        self.pages = QStackedWidget()
        self.pages.setObjectName("wizardPages")
        for index in range(len(STEP_TITLE_KEYS)):
            self.pages.addWidget(self._placeholder(index))
        root.addWidget(self.pages, 1)

        footer = QHBoxLayout()
        self.back_button = QPushButton(tr("wizard_back"))
        self.back_button.setObjectName("wizardBack")
        self.back_button.clicked.connect(self.back)
        footer.addWidget(self.back_button)
        footer.addStretch(1)
        self.next_button = QPushButton(tr("wizard_next"))
        self.next_button.setObjectName("wizardNext")
        self.next_button.clicked.connect(self.next)
        footer.addWidget(self.next_button)
        self.start_button = QPushButton(tr("wizard_start"))
        self.start_button.setObjectName("wizardStart")
        self.start_button.clicked.connect(self._request_start)
        footer.addWidget(self.start_button)
        root.addLayout(footer)

        self.refresh_navigation()

    @staticmethod
    def _placeholder(index):
        page = QWidget()
        page.setObjectName(f"wizardPlaceholder{index}")
        layout = QVBoxLayout(page)
        title = QLabel(tr(STEP_TITLE_KEYS[index]))
        title.setObjectName("wizardPageTitle")
        title.setStyleSheet("font-size:18px;font-weight:600;")
        layout.addWidget(title)
        hint = QLabel(tr(STEP_HINT_KEYS[index]))
        hint.setWordWrap(True)
        layout.addWidget(hint)
        layout.addStretch(1)
        return page

    # ------------------------------------------------------------ structure
    def set_page(self, index: int, widget: QWidget):
        """Replace a placeholder with the real page for that step."""
        old = self.pages.widget(index)
        self.pages.insertWidget(index, widget)
        self.pages.removeWidget(old)
        old.deleteLater()
        self.pages.setCurrentIndex(self.current_step())
        self.refresh_navigation()

    def set_step_validator(self, index: int, validator: Optional[Callable[[], bool]]):
        if validator is None:
            self._validators.pop(index, None)
        else:
            self._validators[index] = validator
        self.refresh_navigation()

    # ----------------------------------------------------------- navigation
    def current_step(self) -> int:
        return self._current

    def step_ready(self, index: int) -> bool:
        validator = self._validators.get(index)
        if validator is None:
            return True
        try:
            return bool(validator())
        except Exception:
            return False

    def can_reach(self, index: int) -> bool:
        """Backward jumps are free; forward jumps need every earlier step ready."""
        if index <= self.current_step():
            return True
        return all(self.step_ready(step) for step in range(index))

    def set_busy(self, busy: bool):
        """Lock navigation while a job runs; the run page owns Stop."""
        self._busy = bool(busy)
        self.refresh_navigation()

    def is_busy(self) -> bool:
        return self._busy

    def set_start_allowed(self, allowed: bool):
        """Hide Start after a finished job until the user prepares a new one."""
        self._start_allowed = bool(allowed)
        self.refresh_navigation()

    def go_to(self, index: int) -> bool:
        if self._busy and index != self.current_step():
            return False
        if not 0 <= index < self.pages.count() or not self.can_reach(index):
            self.refresh_navigation()
            return False
        self._current = index
        self._visited.add(index)
        self.pages.setCurrentIndex(index)
        self.refresh_navigation()
        self.step_changed.emit(index)
        return True

    def next(self) -> bool:
        return self.go_to(self.current_step() + 1)

    def back(self) -> bool:
        return self.go_to(self.current_step() - 1)

    def reset(self):
        """Return to step 1, e.g. for "Translate another video"."""
        self._visited = {STEP_VIDEO}
        self.go_to(STEP_VIDEO)

    def _request_start(self):
        if self.current_step() == STEP_RUN and self.can_start() and not self._busy and self._start_allowed:
            self.start_requested.emit()

    def can_start(self) -> bool:
        return all(self.step_ready(step) for step in range(STEP_RUN))

    def refresh_navigation(self):
        current = self.current_step()
        last = self.pages.count() - 1
        busy = self._busy
        self.back_button.setEnabled(current > 0 and not busy)
        self.next_button.setVisible(current < last)
        self.next_button.setEnabled(current < last and self.step_ready(current) and not busy)
        startable = current == last and not busy and self._start_allowed
        self.start_button.setVisible(startable)
        self.start_button.setEnabled(startable and self.can_start())
        self.classic_button.setEnabled(not busy)
        for index, button in enumerate(self.step_buttons):
            state = "active" if index == current else ("done" if index in self._visited and index < current else "todo")
            button.setChecked(index == current)
            button.setProperty("stepState", state)
            button.setEnabled(self.can_reach(index) and not busy)
            button.style().unpolish(button)
            button.style().polish(button)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and self.next_button.isVisible():
            if self.next_button.isEnabled():
                self.next()
            event.accept()
            return
        super().keyPressEvent(event)
