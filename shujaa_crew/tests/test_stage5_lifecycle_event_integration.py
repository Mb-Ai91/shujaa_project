import pytest

from core.manager.service import ShujaaManager
from core.work.event_store import InMemoryEventStore
from core.work.events import AppendResult
from core.work.models import (
    Execution,
    ExecutionStatus,
)


class UnusedRunner:
    def start(self, command):
        raise AssertionError("Runner must not be called.")


def make_manager(
    *,
    execution_id="exec-stage5-integration",
    event_store=None,
):
    store = event_store or InMemoryEventStore()

    manager = ShujaaManager(
        crew_runner=UnusedRunner(),
        event_store=store,
    )

    execution = Execution(
        execution_id=execution_id,
        work_id=f"work-{execution_id}",
        task_id=f"task-{execution_id}",
    )

    manager.execution_registry.create(execution)

    return manager, execution, store


def test_manager_defaults_to_local_event_store():
    manager = ShujaaManager(
        crew_runner=UnusedRunner(),
    )

    assert isinstance(
        manager.event_store,
        InMemoryEventStore,
    )


def test_applied_transition_emits_canonical_event():
    manager, execution, store = make_manager()

    transition = manager._transition_execution(
        execution.execution_id,
        target_status=ExecutionStatus.RUNNING,
        operation_id="operation-stage5-start",
    )

    entries = store.list()

    assert transition.applied is True
    assert transition.event_append_receipt is not None
    assert (
        transition.event_append_receipt.result
        is AppendResult.APPENDED
    )

    assert len(entries) == 1

    event = entries[0].record

    assert (
        event.event_id
        == "event-execution-transition-"
        "operation-stage5-start"
    )
    assert event.event_type == (
        "execution.transition.applied"
    )
    assert event.entity_type == "execution"
    assert event.entity_id == execution.execution_id
    assert event.source_component == (
        "core.manager.lifecycle"
    )
    assert event.correlation_id == execution.work_id
    assert event.operation_id == (
        "operation-stage5-start"
    )
    assert event.work_id == execution.work_id
    assert event.task_id == execution.task_id
    assert event.execution_id == execution.execution_id
    assert event.payload["disposition"] == "applied"
    assert event.payload["status"] == "running"
    assert event.payload["state_version"] == 1


def test_invalid_transition_emits_no_event():
    manager, execution, store = make_manager(
        execution_id="exec-stage5-invalid",
    )

    with pytest.raises(
        ValueError,
        match="Invalid execution transition",
    ):
        manager._transition_execution(
            execution.execution_id,
            target_status=ExecutionStatus.COMPLETED,
            operation_id="operation-invalid",
        )

    assert store.list() == ()


def test_idempotent_terminal_replay_does_not_duplicate_event():
    manager, execution, store = make_manager(
        execution_id="exec-stage5-replay",
    )

    manager._transition_execution(
        execution.execution_id,
        target_status=ExecutionStatus.RUNNING,
        operation_id="operation-replay-start",
    )

    accepted = manager._transition_execution(
        execution.execution_id,
        target_status=ExecutionStatus.COMPLETED,
        operation_id="operation-replay-complete",
    )

    replay = manager._transition_execution(
        execution.execution_id,
        target_status=ExecutionStatus.COMPLETED,
        operation_id="operation-replay-complete",
    )

    assert accepted.applied is True
    assert replay.applied is False
    assert replay.disposition.value == (
        "idempotent_replay"
    )
    assert replay.event_append_receipt is not None
    assert (
        replay.event_append_receipt.result
        is AppendResult.IDEMPOTENT_REPLAY
    )

    assert len(store.list()) == 2

    event_ids = tuple(
        entry.record.event_id
        for entry in store.list()
    )

    assert event_ids == (
        "event-execution-transition-"
        "operation-replay-start",
        "event-execution-transition-"
        "operation-replay-complete",
    )


def test_losing_terminal_observation_emits_distinct_event():
    manager, execution, store = make_manager(
        execution_id="exec-stage5-losing",
    )

    manager._transition_execution(
        execution.execution_id,
        target_status=ExecutionStatus.RUNNING,
        operation_id="operation-losing-start",
    )

    winner = manager._transition_execution(
        execution.execution_id,
        target_status=ExecutionStatus.COMPLETED,
        operation_id="operation-losing-winner",
    )

    losing = manager._transition_execution(
        execution.execution_id,
        target_status=ExecutionStatus.FAILED,
        operation_id="operation-losing-observation",
    )

    stored = manager.execution_registry.get(
        execution.execution_id
    )
    entries = store.list()
    event = entries[-1].record

    assert winner.applied is True
    assert losing.applied is False
    assert losing.disposition.value == (
        "conflicting_terminal_attempt"
    )
    assert stored is not None
    assert stored.status is ExecutionStatus.COMPLETED
    assert stored.state_version == 2

    assert len(entries) == 3
    assert event.event_type == (
        "execution.transition."
        "conflicting_terminal_attempt"
    )
    assert event.operation_id == (
        "operation-losing-observation"
    )
    assert event.payload["disposition"] == (
        "conflicting_terminal_attempt"
    )
    assert event.payload["attempted_status"] == "failed"
    assert event.payload["winner_status"] == "completed"
    assert event.payload["rejected_at_version"] == 2


def test_event_write_failure_preserves_applied_transition():
    def failing_hasher(payload):
        raise OSError("local append unavailable")

    store = InMemoryEventStore(
        integrity_hasher=failing_hasher,
    )

    manager, execution, _ = make_manager(
        execution_id="exec-stage5-write-failure",
        event_store=store,
    )

    transition = manager._transition_execution(
        execution.execution_id,
        target_status=ExecutionStatus.RUNNING,
        operation_id="operation-write-failure",
    )

    stored = manager.execution_registry.get(
        execution.execution_id
    )

    assert transition.applied is True
    assert transition.event_append_receipt is not None
    assert (
        transition.event_append_receipt.result
        is AppendResult.WRITE_FAILED
    )
    assert (
        transition.event_append_receipt.error_code
        == "OSError"
    )

    assert stored is not None
    assert stored.status is ExecutionStatus.RUNNING
    assert stored.state_version == 1
    assert store.list() == ()


def test_transition_event_omits_raw_error_and_result():
    manager, execution, store = make_manager(
        execution_id="exec-stage5-sensitive",
    )

    manager._transition_execution(
        execution.execution_id,
        target_status=ExecutionStatus.FAILED,
        operation_id="operation-sensitive-failure",
        error="raw-sensitive-error",
        result="raw-sensitive-result",
    )

    event = store.list()[0].record
    payload_text = repr(dict(event.payload))

    assert "error" not in event.payload
    assert "result" not in event.payload
    assert "raw-sensitive-error" not in payload_text
    assert "raw-sensitive-result" not in payload_text
