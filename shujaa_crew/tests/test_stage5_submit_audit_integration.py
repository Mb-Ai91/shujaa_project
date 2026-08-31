from __future__ import annotations

import inspect
import json
from hashlib import sha256
from uuid import uuid4

import pytest

import core.manager.service as manager_service
from core.manager.service import ShujaaManager
from core.policy.contracts import (
    ActorRef,
    AuthorizationContext,
    AuthorizationRequest,
    ResourceRef,
)
from core.policy.evaluator import SinglePrincipalSubmitEvaluator
from core.work.dispatcher import DispatchDecision
from core.work.event_store import (
    AppendReceipt,
    InMemoryAuditStore,
    InMemoryEventStore,
)
from core.work.events import AppendResult, AuditRecord, WorkEvent


_SUBMIT_ACTOR = ActorRef(
    actor_type="service",
    actor_id="test-submit-audit",
)
_SUBMIT_POLICY_VERSION = "test-submit-audit-v1"


def _authorized_submit(manager, command, **kwargs):
    operation_id = f"op-test-submit-audit-{uuid4()}"
    manager.submit_authorization_evaluator = (
        SinglePrincipalSubmitEvaluator(
            principal=_SUBMIT_ACTOR,
            policy_version=_SUBMIT_POLICY_VERSION,
        )
    )
    return manager.submit(
        command,
        authorization_request=AuthorizationRequest(
            actor=_SUBMIT_ACTOR,
            action="work.submit",
            resource=ResourceRef(
                resource_type="work_submission",
                resource_id=operation_id,
            ),
            context=AuthorizationContext(
                request_id=f"request-{operation_id}",
                operation_id=operation_id,
            ),
        ),
        **kwargs,
    )


class UnusedRunner:
    def start(self, command):
        raise AssertionError("Runtime execution must not start.")


class StaticDispatcher:
    def __init__(self):
        self.requests = []

    def dispatch(self, request):
        self.requests.append(request)
        return DispatchDecision(
            executor_id="executor-audit-submit",
            runtime_id="runtime-audit-submit",
        )


class RejectingDispatcher:
    def __init__(self):
        self.request = None

    def dispatch(self, request):
        self.request = request
        raise ValueError("sensitive route rejection detail")


class CapturingThread:
    starts = 0

    def __init__(self, *, target, args, daemon):
        self.target = target
        self.args = args
        self.daemon = daemon

    def start(self):
        type(self).starts += 1


class FailingAuditStore:
    def append(self, record):
        return AppendReceipt(
            result=AppendResult.WRITE_FAILED,
            record_id=record.audit_id,
            error_code="injected_audit_write_failure",
        )

    def append_replay_stable(self, record):
        return AppendReceipt(
            result=AppendResult.APPENDED,
            record_id=record.audit_id,
        )

    def get(self, record_id):
        return None

    def list(self, after_sequence=0, limit=None):
        return ()


def _expected_audit_id(work_id):
    operation_id = f"{work_id}:submit"
    material = json.dumps(
        [operation_id, work_id],
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return f"audit-work-submit-{sha256(material).hexdigest()}"


def _manager(
    *,
    audit_store,
    event_store=None,
    dispatcher=None,
):
    kwargs = {
        "crew_runner": UnusedRunner(),
        "event_store": event_store or InMemoryEventStore(),
        "execution_dispatcher": dispatcher or StaticDispatcher(),
    }

    signature = inspect.signature(ShujaaManager)
    if "audit_store" in signature.parameters:
        kwargs["audit_store"] = audit_store

    manager = ShujaaManager(**kwargs)

    if not hasattr(manager, "audit_store"):
        manager.audit_store = audit_store

    return manager


def _audit(store, audit_id):
    stored = store.get(audit_id)
    assert stored is not None
    assert isinstance(stored.record, AuditRecord)
    return stored.record


@pytest.fixture(autouse=True)
def _capture_threads(monkeypatch):
    CapturingThread.starts = 0
    monkeypatch.setattr(
        manager_service,
        "Thread",
        CapturingThread,
    )


def test_manager_accepts_and_exposes_separate_audit_store():
    signature = inspect.signature(ShujaaManager)
    assert "audit_store" in signature.parameters

    audit_store = InMemoryAuditStore()
    event_store = InMemoryEventStore()
    manager = ShujaaManager(
        crew_runner=UnusedRunner(),
        event_store=event_store,
        audit_store=audit_store,
    )

    assert manager.audit_store is audit_store
    assert manager.event_store is event_store
    assert manager.audit_store is not manager.event_store


def test_accepted_submit_emits_minimal_system_audit_record():
    audit_store = InMemoryAuditStore()
    event_store = InMemoryEventStore()
    manager = _manager(
        audit_store=audit_store,
        event_store=event_store,
    )

    result = _authorized_submit(
        manager,
        "sensitive submit command",
    )

    receipt = result["audit_append_receipt"]
    work_id = result["work_id"]
    expected_id = _expected_audit_id(work_id)

    assert receipt.result == AppendResult.APPENDED
    assert receipt.record_id == expected_id

    audit = _audit(audit_store, expected_id)
    assert audit.action == "work.submit"
    authorization_audit = _audit(
        audit_store,
        result["authorization_audit_append_receipt"].record_id,
    )
    assert audit.actor_type == _SUBMIT_ACTOR.actor_type
    assert audit.actor_id == _SUBMIT_ACTOR.actor_id
    assert audit.resource_type == "work"
    assert audit.resource_id == work_id
    assert audit.outcome == "accepted"
    assert audit.reason_code == "dispatch_accepted"
    assert audit.operation_id == authorization_audit.operation_id
    assert audit.request_id == authorization_audit.request_id
    assert audit.event_id == result["event_append_receipt"].record_id
    assert audit.error_code is None
    assert audit.policy_version == _SUBMIT_POLICY_VERSION
    assert audit.approval_id is None
    assert "sensitive submit command" not in repr(audit)


def test_submit_separates_event_and_audit_receipts_and_stores():
    audit_store = InMemoryAuditStore()
    event_store = InMemoryEventStore()
    manager = _manager(
        audit_store=audit_store,
        event_store=event_store,
    )

    result = _authorized_submit(
        manager,
        "separate receipt command",
    )

    event_receipt = result["event_append_receipt"]
    audit_receipt = result["audit_append_receipt"]

    assert event_receipt is not audit_receipt
    assert event_receipt.record_id != audit_receipt.record_id
    assert len(event_store.list()) == 1
    assert len(audit_store.list()) == 2
    assert isinstance(event_store.list()[0].record, WorkEvent)
    assert isinstance(audit_store.list()[0].record, AuditRecord)


def test_dispatch_rejection_emits_audit_without_partial_state():
    audit_store = InMemoryAuditStore()
    event_store = InMemoryEventStore()
    dispatcher = RejectingDispatcher()
    manager = _manager(
        audit_store=audit_store,
        event_store=event_store,
        dispatcher=dispatcher,
    )

    with pytest.raises(ValueError) as caught:
        _authorized_submit(
            manager,
            "sensitive rejected command",
        )

    error = caught.value
    assert type(error).__name__ == "AuditedDispatchRejectionError"
    assert str(error) == "sensitive route rejection detail"
    assert error.reason_code == "dispatch_rejected"
    assert error.audit_append_receipt.result == AppendResult.APPENDED

    request = dispatcher.request
    assert request is not None
    assert manager.work_registry.get(request.work_id) is None
    assert manager.task_store.get(request.task_id) is None
    assert manager.execution_registry.get(request.execution_id) is None
    assert event_store.list() == ()
    assert CapturingThread.starts == 0

    audit = _audit(
        audit_store,
        error.audit_append_receipt.record_id,
    )
    assert audit.action == "work.submit"
    assert audit.resource_type == "work"
    assert audit.resource_id == request.work_id
    assert audit.outcome == "rejected"
    assert audit.reason_code == "dispatch_rejected"
    assert audit.error_code == "ValueError"
    assert audit.event_id is None
    assert "sensitive rejected command" not in repr(audit)
    assert "sensitive route rejection detail" not in repr(audit)


def test_dispatch_rejection_preserves_value_error_compatibility():
    audit_store = InMemoryAuditStore()
    manager = _manager(
        audit_store=audit_store,
        dispatcher=RejectingDispatcher(),
    )

    with pytest.raises(
        ValueError,
        match="sensitive route rejection detail",
    ) as caught:
        _authorized_submit(manager, "rejected command")

    assert caught.value.audit_append_receipt is not None
    assert caught.value.reason_code == "dispatch_rejected"


def test_audit_write_failure_does_not_change_accepted_submit():
    audit_store = FailingAuditStore()
    event_store = InMemoryEventStore()
    dispatcher = StaticDispatcher()
    manager = _manager(
        audit_store=audit_store,
        event_store=event_store,
        dispatcher=dispatcher,
    )

    result = _authorized_submit(
        manager,
        "accepted despite audit failure",
    )

    assert result["status"] == "accepted"
    assert result["event_append_receipt"].result == (
        AppendResult.APPENDED
    )
    receipt = result["audit_append_receipt"]
    assert receipt.result == AppendResult.WRITE_FAILED
    assert receipt.error_code == "injected_audit_write_failure"
    assert manager.work_registry.get(result["work_id"]) is not None
    assert manager.task_store.get(result["task_id"]) is not None
    assert (
        manager.execution_registry.get(result["execution_id"])
        is not None
    )
    assert CapturingThread.starts == 1
    assert len(dispatcher.requests) == 1


def test_audit_write_failure_does_not_replace_dispatch_rejection():
    manager = _manager(
        audit_store=FailingAuditStore(),
        dispatcher=RejectingDispatcher(),
    )

    with pytest.raises(
        ValueError,
        match="sensitive route rejection detail",
    ) as caught:
        _authorized_submit(
            manager,
            "rejected despite audit failure",
        )

    error = caught.value
    assert type(error).__name__ == "AuditedDispatchRejectionError"
    assert error.reason_code == "dispatch_rejected"
    assert error.audit_append_receipt.result == (
        AppendResult.WRITE_FAILED
    )
    assert error.audit_append_receipt.error_code == (
        "injected_audit_write_failure"
    )


def test_independent_same_command_submits_create_distinct_audits():
    audit_store = InMemoryAuditStore()
    manager = _manager(audit_store=audit_store)

    first = _authorized_submit(manager, "same command")
    second = _authorized_submit(manager, "same command")

    assert first["work_id"] != second["work_id"]
    assert first["audit_append_receipt"].record_id != (
        second["audit_append_receipt"].record_id
    )
    assert len(audit_store.list()) == 4
    assert CapturingThread.starts == 2
