from __future__ import annotations

import pytest

import core.manager.service as manager_service
from core.manager.service import ShujaaManager
from core.tasks.store import TaskRecord
from core.work.dispatcher import DispatchDecision
from core.work.event_store import (
    AppendReceipt,
    InMemoryEventStore,
)
from core.work.events import AppendResult
from core.work.models import (
    Execution,
    ExecutionStatus,
    RetrySafety,
)


class UnusedRunner:
    def start(self, command):
        raise AssertionError(
            "Runtime execution is replaced by CapturingThread."
        )


class CapturingThread:
    starts = 0

    def __init__(self, *, target, args, daemon):
        self.target = target
        self.args = args
        self.daemon = daemon

    def start(self):
        type(self).starts += 1


class StaticDispatcher:
    def __init__(self):
        self.requests = []

    def dispatch(self, request):
        self.requests.append(request)
        return DispatchDecision(
            executor_id="executor-safe",
            agent_id="agent-safe",
            runtime_id="agent-executor",
        )


class RejectingDispatcher:
    def dispatch(self, request):
        raise ValueError("route rejected")


class FailingEventStore:
    def append(self, record):
        return AppendReceipt(
            result=AppendResult.WRITE_FAILED,
            record_id=record.event_id,
            error_code="injected_write_failure",
        )

    def get(self, record_id):
        return None

    def list(self):
        return []


@pytest.fixture
def captured_threads(monkeypatch):
    CapturingThread.starts = 0
    monkeypatch.setattr(
        manager_service,
        "Thread",
        CapturingThread,
    )
    return CapturingThread


def _event_from_store(store, record_id):
    stored = store.get(record_id)
    assert stored is not None
    return (
        stored.record
        if hasattr(stored, "record")
        else stored
    )


def _retry_manager(*, event_store):
    dispatcher = StaticDispatcher()
    manager = ShujaaManager(
        crew_runner=UnusedRunner(),
        execution_dispatcher=dispatcher,
        event_store=event_store,
    )
    task = TaskRecord(
        task_id="task-retry-handoff",
        work_id="work-retry-handoff",
        command="sensitive retry command",
        status="failed",
        error="sensitive original error",
    )
    source = Execution(
        execution_id="exec-retry-handoff-source",
        work_id=task.work_id,
        task_id=task.task_id,
        status=ExecutionStatus.FAILED,
        retry_safety=RetrySafety.DECLARED_SAFE,
        requested_agent_id="requested-agent",
        required_capability="capability.logical",
    )
    manager.task_store.create(task)
    manager.execution_registry.create(source)
    return manager, dispatcher, source


def test_submit_emits_safe_canonical_dispatch_event(
    captured_threads,
):
    store = InMemoryEventStore()
    dispatcher = StaticDispatcher()
    manager = ShujaaManager(
        crew_runner=UnusedRunner(),
        execution_dispatcher=dispatcher,
        event_store=store,
    )

    result = manager.submit(
        "top secret command",
        requested_agent_id="requested-agent",
        required_capability="capability.logical",
    )

    receipt = result["event_append_receipt"]

    assert receipt.result == AppendResult.APPENDED
    assert receipt.record_id == (
        "event-execution-dispatched-"
        f'{result["execution_id"]}'
    )

    event = _event_from_store(
        store,
        receipt.record_id,
    )

    assert event.event_type == "execution.dispatched"
    assert event.entity_type == "execution"
    assert event.entity_id == result["execution_id"]
    assert event.work_id == result["work_id"]
    assert event.task_id == result["task_id"]
    assert event.execution_id == result["execution_id"]
    assert event.correlation_id == result["work_id"]
    assert event.source_component.strip()
    assert event.capability_asset_id == "capability.logical"
    assert event.payload["executor_id"] == "executor-safe"
    assert event.payload["runtime_id"] == "agent-executor"
    assert event.payload["agent_id"] == "agent-safe"
    assert (
        event.payload["requested_agent_id"]
        == "requested-agent"
    )
    assert "command" not in event.payload
    assert "result" not in event.payload
    assert "error" not in event.payload
    assert "top secret command" not in repr(event.payload)
    assert captured_threads.starts == 1


def test_dispatch_event_is_appended_after_thread_handoff(
    monkeypatch,
):
    order = []

    class OrderedStore(InMemoryEventStore):
        def append(self, record):
            order.append("event_append")
            return super().append(record)

    class OrderedThread(CapturingThread):
        def start(self):
            order.append("thread_start")
            super().start()

    monkeypatch.setattr(
        manager_service,
        "Thread",
        OrderedThread,
    )

    manager = ShujaaManager(
        crew_runner=UnusedRunner(),
        execution_dispatcher=StaticDispatcher(),
        event_store=OrderedStore(),
    )

    manager.submit("ordered handoff")

    assert order == [
        "thread_start",
        "event_append",
    ]


def test_event_write_failure_is_structured_and_handoff_continues(
    captured_threads,
):
    manager = ShujaaManager(
        crew_runner=UnusedRunner(),
        execution_dispatcher=StaticDispatcher(),
        event_store=FailingEventStore(),
    )

    result = manager.submit("handoff despite event failure")
    receipt = result["event_append_receipt"]

    assert receipt.result == AppendResult.WRITE_FAILED
    assert receipt.error_code == "injected_write_failure"
    assert captured_threads.starts == 1


def test_retry_handoff_emits_event_and_returns_receipt(
    captured_threads,
):
    store = InMemoryEventStore()
    manager, dispatcher, source = _retry_manager(
        event_store=store,
    )

    admission = manager.retry_task(
        source.execution_id,
        operation_id="retry-handoff-operation",
    )

    assert admission.applied is True
    assert admission.event_append_receipt is not None
    assert (
        admission.event_append_receipt.result
        == AppendResult.APPENDED
    )

    event = _event_from_store(
        store,
        admission.event_append_receipt.record_id,
    )

    assert event.event_type == "execution.dispatched"
    assert event.execution_id == (
        admission.execution.execution_id
    )
    assert event.work_id == source.work_id
    assert event.task_id == source.task_id
    assert event.operation_id == "retry-handoff-operation"
    assert event.payload["executor_id"] == "executor-safe"
    assert "command" not in event.payload
    assert "error" not in event.payload
    assert captured_threads.starts == 1
    assert len(dispatcher.requests) == 1


def test_retry_replay_does_not_duplicate_dispatch_event(
    captured_threads,
):
    store = InMemoryEventStore()
    manager, dispatcher, source = _retry_manager(
        event_store=store,
    )

    first = manager.retry_task(
        source.execution_id,
        operation_id="retry-replay-operation",
    )
    replay = manager.retry_task(
        source.execution_id,
        operation_id="retry-replay-operation",
    )

    assert first.event_append_receipt is not None
    assert replay.applied is False
    assert replay.event_append_receipt is None
    assert len(store.list()) == 1
    assert len(dispatcher.requests) == 1
    assert captured_threads.starts == 1


def test_dispatch_rejection_emits_no_handoff_event():
    store = InMemoryEventStore()
    manager = ShujaaManager(
        crew_runner=UnusedRunner(),
        execution_dispatcher=RejectingDispatcher(),
        event_store=store,
    )

    with pytest.raises(
        ValueError,
        match="route rejected",
    ):
        manager.submit("rejected handoff")

    assert store.list() == ()
