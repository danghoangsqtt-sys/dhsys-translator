"""Map existing task events to presentation-only workflow states."""

from typing import Callable


WORKFLOW_IDLE = "idle"
WORKFLOW_RUNNING = "running"
WORKFLOW_ERROR = "error"
WORKFLOW_COMPLETE = "complete"

WORKFLOW_STATUS_LABELS = {
    WORKFLOW_IDLE: "Workflow ready",
    WORKFLOW_RUNNING: "Workflow in progress",
    WORKFLOW_ERROR: "Workflow needs attention",
    WORKFLOW_COMPLETE: "Workflow complete",
}


def state_for_action_status(status: str, current_state: str) -> str:
    """Return the presentation state for an existing application status value."""
    if status == "ing":
        return WORKFLOW_RUNNING
    if status == "stop":
        return WORKFLOW_IDLE
    if status == "end":
        return WORKFLOW_ERROR if current_state == WORKFLOW_ERROR else WORKFLOW_COMPLETE
    return current_state


def state_for_message_type(message_type: str, current_state: str) -> str:
    """Return the presentation state for a ``SignMsg.type`` without parsing logs."""
    if message_type in {"error", "ffmpeg"}:
        return WORKFLOW_ERROR
    if message_type == "end":
        return state_for_action_status("end", current_state)
    if message_type in {"logs", "set_precent", "succeed"}:
        return WORKFLOW_RUNNING if current_state != WORKFLOW_ERROR else current_state
    return current_state


class WorkflowStatePresenter:
    """Publish a mapped state to a view callback without owning task behavior."""

    def __init__(self, apply_state: Callable[[str], None]):
        self._apply_state = apply_state
        self.current_state = WORKFLOW_IDLE
        self._apply_state(self.current_state)

    def handle_action_status(self, status: str) -> str:
        return self._set_state(state_for_action_status(status, self.current_state))

    def handle_message_type(self, message_type: str) -> str:
        return self._set_state(state_for_message_type(message_type, self.current_state))

    def _set_state(self, state: str) -> str:
        if state != self.current_state:
            self.current_state = state
            self._apply_state(state)
        return self.current_state
