from videotrans.ui.workflow_state import (
    WORKFLOW_COMPLETE,
    WORKFLOW_ERROR,
    WORKFLOW_IDLE,
    WORKFLOW_RUNNING,
    WorkflowStatePresenter,
    state_for_action_status,
    state_for_message_type,
)


def test_action_status_mapping_preserves_an_error_at_end():
    assert state_for_action_status("ing", WORKFLOW_IDLE) == WORKFLOW_RUNNING
    assert state_for_action_status("stop", WORKFLOW_RUNNING) == WORKFLOW_IDLE
    assert state_for_action_status("end", WORKFLOW_RUNNING) == WORKFLOW_COMPLETE
    assert state_for_action_status("end", WORKFLOW_ERROR) == WORKFLOW_ERROR


def test_message_mapping_does_not_guess_from_unknown_messages():
    assert state_for_message_type("logs", WORKFLOW_IDLE) == WORKFLOW_RUNNING
    assert state_for_message_type("error", WORKFLOW_RUNNING) == WORKFLOW_ERROR
    assert state_for_message_type("ffmpeg", WORKFLOW_RUNNING) == WORKFLOW_ERROR
    assert state_for_message_type("unknown", WORKFLOW_RUNNING) == WORKFLOW_RUNNING
    assert state_for_message_type("succeed", WORKFLOW_ERROR) == WORKFLOW_ERROR


def test_presenter_notifies_only_when_the_view_state_changes():
    rendered = []
    presenter = WorkflowStatePresenter(rendered.append)

    presenter.handle_action_status("ing")
    presenter.handle_message_type("logs")
    presenter.handle_message_type("error")
    presenter.handle_action_status("end")
    presenter.handle_action_status("stop")

    assert rendered == [WORKFLOW_IDLE, WORKFLOW_RUNNING, WORKFLOW_ERROR, WORKFLOW_IDLE]
    assert presenter.current_state == WORKFLOW_IDLE
