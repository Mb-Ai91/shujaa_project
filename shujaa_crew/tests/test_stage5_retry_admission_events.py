from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256

import pytest

import core.manager.service as manager_service
from core.manager.service import ShujaaManager
from core.tasks.store import TaskRecord
from core.work.dispatcher import DispatchDecision
from core.work.event_store import AppendReceipt, InMemoryEventStore
from core.work.events import AppendResult
from core.work.execution_registry import InMemoryExecutionRegistry
from core.work.models import Execution, ExecutionStatus, RetrySafety


class UnusedRunner:
    def start(self, command):
        raise AssertionError("Runtime execution must not start.")


class StaticDispatcher:
    def __init__(self):
        self.requests = []

    def dispatch(self, request):
        self.requests.append(request)
        return DispatchDecision(
            executor_id="executor-retry-safe",
            runtime_id="runtime-retry-safe",
        )


class CapturingThread:
    starts = 0
    order = None

    def __init__(self, *, target, args, daemon):
        self.target = target
        self.args = args
        self.daemon = daemon

    def start(self):
        type(self).starts += 1
        if type(self).order is not None:
            type(self).order.append("runtime_handoff")


class FailingReplayStableStore:
    def append(self, record):
        return AppendReceipt(
            result=AppendResult.WRITE_FAILED,
            record_id=record.event_id,
            error_code="injected_dispatch_write_failure",
        )

    def append_replay_stable(self, record):
        return AppendReceipt(
            result=AppendResult.WRITE_FAILED,
            record_id=record.event_id,
            error_code="injected_admission_write_failure",
        )

    def get(self, record_id):
        return None

    def list(self, after_sequence=0, limit=None):
        return ()


def _expected_event_id(operation_id, source_execution_id):
    material = json.dumps(
        [operation_id, source_execution_id],
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return (
        "event-execution-retry-admission-"
        f"{sha256(material).hexdigest()}"
    )


def _event(store, record_id):
    stored = store.get(record_id)
    assert stored is not None
    return stored.record


def _manager(*, event_store=None, execution_registry=None):
    manager = ShujaaManager(
        crew_runner=UnusedRunner(),
        event_store=event_store or InMemoryEventStore(),
    )
    if execution_registry is not None:
        manager.execution_registry = execution_registry
    return manager


def _source(
    manager,
    suffix,
    *,
    status=ExecutionStatus.FAILED,
    retry_safety=RetrySafety.DECLARED_SAFE,
    with_task=False,
):
    execution = Execution(
        execution_id=f"exec-source-{suffix}",
        work_id=f"work-{suffix}",
        task_id=f"task-{suffix}",
        status=status,
        retry_safety=retry_safety,
        requested_agent_id="agent-original",
        required_capability="capability.logical",
    )
    manager.execution_registry.create(execution)

    if with_task:
        manager.task_store.create(
            TaskRecord(
                task_id=execution.task_id,
                work_id=execution.work_id,
                command="sensitive retry command",
                status=status.value,
                error="sensitive original error",
            )
        )

    return execution


def _assert_outcome(outcome):
    assert type(outcome).__name__ == "RetryEventOutcome"
    assert outcome.admission_result is not None
    assert outcome.admission_event_append_receipt is not None


def test_direct_admission_emits_deterministic_minimal_event():
    store = InMemoryEventStore()
    manager = _manager(event_store=store)
    source = _source(manager, "direct")
    operation_id = "retry-operation-direct"

    outcome = manager.admit_retry(
        source.execution_id,
        operation_id=operation_id,
    )

    _assert_outcome(outcome)
    assert outcome.applied is True
    assert outcome.disposition.value == "applied"
    assert outcome.event_append_receipt is None

    receipt = outcome.admission_event_append_receipt
    expected_id = _expected_event_id(
        operation_id,
        source.execution_id,
    )
    assert receipt.result == AppendResult.APPENDED
    assert receipt.record_id == expected_id

    event = _event(store, expected_id)
    assert event.event_type == "execution.retry_admission.applied"
    assert event.entity_type == "execution"
    assert event.entity_id == source.execution_id
    assert event.source_component == "core.manager.retry_admission"
    assert event.operation_id == operation_id
    assert event.work_id == source.work_id
    assert event.task_id == source.task_id
    assert event.execution_id == outcome.execution.execution_id
    assert event.payload == {"disposition": "applied"}
    assert "command" not in repr(event.payload)
    assert "result" not in repr(event.payload)
    assert "error" not in repr(event.payload)


def test_replay_uses_canonical_applied_event_without_duplicate():
    store = InMemoryEventStore()
    manager = _manager(event_store=store)
    source = _source(manager, "replay")
    operation_id = "retry-operation-replay"

    first = manager.admit_retry(
        source.execution_id,
        operation_id=operation_id,
    )
    replay = manager.admit_retry(
        source.execution_id,
        operation_id=operation_id,
    )

    _assert_outcome(first)
    _assert_outcome(replay)
    assert first.disposition.value == "applied"
    assert replay.disposition.value == "idempotent_replay"
    assert first.admission_event_append_receipt.result == (
        AppendResult.APPENDED
    )
    assert replay.admission_event_append_receipt.result == (
        AppendResult.IDEMPOTENT_REPLAY
    )
    assert len(store.list()) == 1

    event = _event(
        store,
        first.admission_event_append_receipt.record_id,
    )
    assert event.event_type == "execution.retry_admission.applied"
    assert event.payload == {"disposition": "applied"}


def test_conflicting_operation_emits_independent_conflict_event():
    store = InMemoryEventStore()
    manager = _manager(event_store=store)
    source = _source(manager, "conflict")

    first = manager.admit_retry(
        source.execution_id,
        operation_id="retry-operation-winner",
    )
    conflict = manager.admit_retry(
        source.execution_id,
        operation_id="retry-operation-conflict",
    )

    _assert_outcome(first)
    _assert_outcome(conflict)
    assert conflict.applied is False
    assert conflict.disposition.value == "conflicting_retry"
    assert conflict.execution == first.execution
    assert conflict.admission_event_append_receipt.result == (
        AppendResult.APPENDED
    )
    assert len(store.list()) == 2
    assert len(
        manager.execution_registry.list_by_task(source.task_id)
    ) == 2

    event = _event(
        store,
        conflict.admission_event_append_receipt.record_id,
    )
    assert event.event_type == (
        "execution.retry_admission.conflicting_retry"
    )
    assert event.execution_id == first.execution.execution_id
    assert event.payload == {"disposition": "conflicting_retry"}


def test_retry_task_separates_admission_and_dispatch_receipts(
    monkeypatch,
):
    order = []

    class OrderedStore(InMemoryEventStore):
        def append_replay_stable(self, record):
            order.append("admission_event")
            return super().append_replay_stable(record)

        def append(self, record):
            order.append("dispatch_event")
            return super().append(record)

    CapturingThread.starts = 0
    CapturingThread.order = order
    monkeypatch.setattr(
        manager_service,
        "Thread",
        CapturingThread,
    )

    store = OrderedStore()
    dispatcher = StaticDispatcher()
    manager = ShujaaManager(
        crew_runner=UnusedRunner(),
        execution_dispatcher=dispatcher,
        event_store=store,
    )
    source = _source(manager, "retry-task", with_task=True)

    outcome = manager.retry_task(
        source.execution_id,
        operation_id="retry-operation-task",
    )

    _assert_outcome(outcome)
    assert outcome.admission_event_append_receipt.result == (
        AppendResult.APPENDED
    )
    assert outcome.event_append_receipt is not None
    assert outcome.event_append_receipt.result == AppendResult.APPENDED
    assert outcome.admission_event_append_receipt.record_id != (
        outcome.event_append_receipt.record_id
    )
    assert order == [
        "admission_event",
        "runtime_handoff",
        "dispatch_event",
    ]
    assert CapturingThread.starts == 1
    assert len(dispatcher.requests) == 1


def test_retry_denied_by_safety_emits_redacted_reason():
    store = InMemoryEventStore()
    manager = _manager(event_store=store)
    source = _source(
        manager,
        "denied-safety",
        retry_safety=RetrySafety.DENY,
    )
    operation_id = "retry-operation-denied-safety"

    with pytest.raises(ValueError) as caught:
        manager.admit_retry(
            source.execution_id,
            operation_id=operation_id,
        )

    error = caught.value
    assert type(error).__name__ == "RetryAdmissionDeniedError"
    assert error.reason_code == "retry_not_declared_safe"
    assert error.admission_event_append_receipt.result == (
        AppendResult.APPENDED
    )

    event = _event(
        store,
        error.admission_event_append_receipt.record_id,
    )
    assert event.event_type == "execution.retry_admission.denied"
    assert event.payload == {
        "disposition": "denied",
        "reason_code": "retry_not_declared_safe",
    }
    assert "sensitive" not in repr(event.payload)


@pytest.mark.parametrize(
    "status",
    (ExecutionStatus.RUNNING, ExecutionStatus.COMPLETED),
)
def test_nonretryable_status_emits_structured_denial(status):
    store = InMemoryEventStore()
    manager = _manager(event_store=store)
    source = _source(
        manager,
        f"denied-{status.value}",
        status=status,
    )

    with pytest.raises(ValueError) as caught:
        manager.admit_retry(
            source.execution_id,
            operation_id=f"retry-denied-{status.value}",
        )

    error = caught.value
    assert type(error).__name__ == "RetryAdmissionDeniedError"
    assert error.reason_code == "status_not_retryable"
    assert error.admission_event_append_receipt.result == (
        AppendResult.APPENDED
    )


def test_missing_source_emits_structured_denial():
    store = InMemoryEventStore()
    manager = _manager(event_store=store)

    with pytest.raises(ValueError) as caught:
        manager.admit_retry(
            "exec-source-missing",
            operation_id="retry-operation-missing-source",
        )

    error = caught.value
    assert type(error).__name__ == "RetryAdmissionDeniedError"
    assert error.reason_code == "source_execution_not_found"
    assert error.admission_event_append_receipt.result == (
        AppendResult.APPENDED
    )
    event = _event(
        store,
        error.admission_event_append_receipt.record_id,
    )
    assert event.entity_id == "exec-source-missing"
    assert event.work_id is None
    assert event.task_id is None


def test_invalid_operation_id_is_rejected_without_event():
    store = InMemoryEventStore()
    manager = _manager(event_store=store)
    source = _source(manager, "invalid-operation")

    with pytest.raises(ValueError) as caught:
        manager.admit_retry(
            source.execution_id,
            operation_id=" ",
        )

    error = caught.value
    assert type(error).__name__ == "RetryAdmissionDeniedError"
    assert error.reason_code == "invalid_operation_id"
    assert error.admission_event_append_receipt is None
    assert store.list() == ()


def test_concurrent_same_operation_is_replay_stable():
    registry = InMemoryExecutionRegistry()
    store = InMemoryEventStore()
    first_manager = _manager(
        event_store=store,
        execution_registry=registry,
    )
    second_manager = _manager(
        event_store=store,
        execution_registry=registry,
    )
    source = _source(first_manager, "concurrent-replay")

    def admit(manager):
        return manager.admit_retry(
            source.execution_id,
            operation_id="retry-operation-concurrent-shared",
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(
            pool.map(admit, (first_manager, second_manager))
        )

    assert {
        outcome.disposition.value for outcome in outcomes
    } == {"applied", "idempotent_replay"}
    assert {
        outcome.admission_event_append_receipt.result
        for outcome in outcomes
    } == {
        AppendResult.APPENDED,
        AppendResult.IDEMPOTENT_REPLAY,
    }
    assert len(store.list()) == 1
    assert len(registry.list_by_task(source.task_id)) == 2


def test_concurrent_different_operations_emit_conflict_event():
    registry = InMemoryExecutionRegistry()
    store = InMemoryEventStore()
    first_manager = _manager(
        event_store=store,
        execution_registry=registry,
    )
    second_manager = _manager(
        event_store=store,
        execution_registry=registry,
    )
    source = _source(first_manager, "concurrent-conflict")

    def admit(request):
        manager, operation_id = request
        return manager.admit_retry(
            source.execution_id,
            operation_id=operation_id,
        )

    requests = (
        (first_manager, "retry-concurrent-a"),
        (second_manager, "retry-concurrent-b"),
    )
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(admit, requests))

    assert {
        outcome.disposition.value for outcome in outcomes
    } == {"applied", "conflicting_retry"}
    assert all(
        outcome.admission_event_append_receipt.result
        == AppendResult.APPENDED
        for outcome in outcomes
    )
    assert len(store.list()) == 2
    assert len(registry.list_by_task(source.task_id)) == 2


def test_admission_write_failure_does_not_change_winner():
    store = FailingReplayStableStore()
    manager = _manager(event_store=store)
    source = _source(manager, "write-failed-applied")

    outcome = manager.admit_retry(
        source.execution_id,
        operation_id="retry-operation-write-failed",
    )

    _assert_outcome(outcome)
    assert outcome.applied is True
    assert outcome.disposition.value == "applied"
    assert outcome.admission_event_append_receipt.result == (
        AppendResult.WRITE_FAILED
    )
    assert outcome.admission_event_append_receipt.error_code == (
        "injected_admission_write_failure"
    )
    assert len(
        manager.execution_registry.list_by_task(source.task_id)
    ) == 2


def test_denial_write_failure_does_not_replace_denial():
    store = FailingReplayStableStore()
    manager = _manager(event_store=store)
    source = _source(
        manager,
        "write-failed-denied",
        retry_safety=RetrySafety.DENY,
    )

    with pytest.raises(ValueError) as caught:
        manager.admit_retry(
            source.execution_id,
            operation_id="retry-denied-write-failed",
        )

    error = caught.value
    assert type(error).__name__ == "RetryAdmissionDeniedError"
    assert error.reason_code == "retry_not_declared_safe"
    assert error.admission_event_append_receipt.result == (
        AppendResult.WRITE_FAILED
    )
    assert error.admission_event_append_receipt.error_code == (
        "injected_admission_write_failure"
    )
    assert manager.execution_registry.list_by_task(
        source.task_id
    ) == [source]
