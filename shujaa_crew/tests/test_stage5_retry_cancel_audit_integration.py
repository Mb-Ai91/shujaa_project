from __future__ import annotations

import inspect
import json
from hashlib import sha256

import pytest

from core.manager.service import ShujaaManager
from core.tasks.store import TaskRecord
from core.work.event_store import (
    AppendReceipt,
    InMemoryAuditStore,
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
        raise AssertionError("Runtime execution is not expected.")


class FailingAuditStore:
    def append(self, record):
        return AppendReceipt(
            result=AppendResult.WRITE_FAILED,
            record_id=record.audit_id,
            error_code="injected_audit_write_failure",
        )

    def append_replay_stable(self, record):
        return self.append(record)

    def get(self, record_id):
        return None

    def list(self, after_sequence=0, limit=None):
        return ()


def _manager(*, audit_store=None, event_store=None):
    return ShujaaManager(
        crew_runner=UnusedRunner(),
        audit_store=(audit_store or InMemoryAuditStore()),
        event_store=(event_store or InMemoryEventStore()),
    )


def _seed_source(
    manager,
    suffix,
    *,
    status=ExecutionStatus.FAILED,
    retry_safety=RetrySafety.DECLARED_SAFE,
):
    task = TaskRecord(
        task_id=f"task-{suffix}",
        work_id=f"work-{suffix}",
        command="sensitive command must not enter audit",
        status=status.value,
        error="sensitive source error must not enter audit",
    )
    execution = Execution(
        execution_id=f"exec-{suffix}",
        work_id=task.work_id,
        task_id=task.task_id,
        status=status,
        retry_safety=retry_safety,
        error=task.error,
    )
    manager.task_store.create(task)
    manager.execution_registry.create(execution)
    return task, execution


def _expected_audit_id(prefix, operation_id, resource_id):
    material = json.dumps(
        [operation_id, resource_id],
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return f"{prefix}{sha256(material).hexdigest()}"


def _audit(store, record_id):
    stored = store.get(record_id)
    assert stored is not None
    return stored.record


def test_retry_acceptance_emits_minimal_linked_audit():
    audit_store = InMemoryAuditStore()
    manager = _manager(audit_store=audit_store)
    _, source = _seed_source(manager, "retry-audit-accepted")
    operation_id = "op-retry-audit-accepted"

    outcome = manager.admit_retry(
        source.execution_id,
        operation_id=operation_id,
    )

    receipt = outcome.audit_append_receipt
    expected_id = _expected_audit_id(
        "audit-execution-retry-",
        operation_id,
        source.execution_id,
    )
    assert receipt.result == AppendResult.APPENDED
    assert receipt.record_id == expected_id

    audit = _audit(audit_store, expected_id)
    assert audit.action == "execution.retry"
    assert audit.actor_type == "system"
    assert audit.actor_id == "shujaa_manager"
    assert audit.resource_type == "execution"
    assert audit.resource_id == source.execution_id
    assert audit.operation_id == operation_id
    assert audit.outcome == "accepted"
    assert audit.reason_code == "retry_admitted"
    assert audit.event_id == (
        outcome.admission_event_append_receipt.record_id
    )
    rendered = repr(audit)
    assert "sensitive command" not in rendered
    assert "sensitive source error" not in rendered


def test_retry_denial_exposes_separate_event_and_audit_receipts():
    audit_store = InMemoryAuditStore()
    manager = _manager(audit_store=audit_store)
    _, source = _seed_source(
        manager,
        "retry-audit-denied",
        retry_safety=RetrySafety.DENY,
    )
    operation_id = "op-retry-audit-denied"

    with pytest.raises(ValueError) as caught:
        manager.admit_retry(
            source.execution_id,
            operation_id=operation_id,
        )

    error = caught.value
    assert type(error).__name__ == "RetryAdmissionDeniedError"
    assert error.reason_code == "retry_not_declared_safe"
    assert error.admission_event_append_receipt is not None
    assert error.audit_append_receipt is not None
    assert error.audit_append_receipt.record_id != (
        error.admission_event_append_receipt.record_id
    )

    audit = _audit(
        audit_store,
        error.audit_append_receipt.record_id,
    )
    assert audit.outcome == "rejected"
    assert audit.reason_code == "retry_not_declared_safe"
    assert audit.event_id == (
        error.admission_event_append_receipt.record_id
    )
    assert "sensitive" not in repr(audit)


def test_retry_audit_replay_is_stable_without_duplicate():
    audit_store = InMemoryAuditStore()
    manager = _manager(audit_store=audit_store)
    _, source = _seed_source(manager, "retry-audit-replay")
    operation_id = "op-retry-audit-replay"

    first = manager.admit_retry(
        source.execution_id,
        operation_id=operation_id,
    )
    replay = manager.admit_retry(
        source.execution_id,
        operation_id=operation_id,
    )

    assert first.audit_append_receipt.result == (
        AppendResult.APPENDED
    )
    assert replay.audit_append_receipt.result == (
        AppendResult.IDEMPOTENT_REPLAY
    )
    assert first.audit_append_receipt.record_id == (
        replay.audit_append_receipt.record_id
    )
    assert len(audit_store.list()) == 1


def test_retry_audit_write_failure_does_not_change_admission():
    manager = _manager(audit_store=FailingAuditStore())
    _, source = _seed_source(manager, "retry-audit-failure")

    outcome = manager.admit_retry(
        source.execution_id,
        operation_id="op-retry-audit-failure",
    )

    assert outcome.applied is True
    assert outcome.audit_append_receipt.result == (
        AppendResult.WRITE_FAILED
    )
    assert outcome.audit_append_receipt.error_code == (
        "injected_audit_write_failure"
    )
    assert len(
        manager.execution_registry.list_by_task(source.task_id)
    ) == 2


def test_cancel_requires_distinct_explicit_operation_ids():
    signature = inspect.signature(ShujaaManager.cancel_task)
    cancel_parameter = signature.parameters["cancel_operation_id"]
    cleanup_parameter = signature.parameters["cleanup_operation_id"]

    assert cancel_parameter.kind is inspect.Parameter.KEYWORD_ONLY
    assert cleanup_parameter.kind is inspect.Parameter.KEYWORD_ONLY
    assert cancel_parameter.default is inspect.Parameter.empty
    assert cleanup_parameter.default is inspect.Parameter.empty


def test_cancel_acceptance_emits_minimal_linked_audit():
    audit_store = InMemoryAuditStore()
    manager = _manager(audit_store=audit_store)
    task, execution = _seed_source(
        manager,
        "cancel-audit-accepted",
        status=ExecutionStatus.QUEUED,
    )
    cancel_operation_id = "op-cancel-request-accepted"

    response = manager.cancel_task(
        task.task_id,
        cancel_operation_id=cancel_operation_id,
        cleanup_operation_id="op-cancel-cleanup-accepted",
    )

    assert response["status"] == "cancelled"
    receipt = response["audit_append_receipt"]
    expected_id = _expected_audit_id(
        "audit-task-cancel-",
        cancel_operation_id,
        task.task_id,
    )
    assert receipt.result == AppendResult.APPENDED
    assert receipt.record_id == expected_id

    audit = _audit(audit_store, expected_id)
    assert audit.action == "task.cancel"
    assert audit.actor_type == "system"
    assert audit.actor_id == "shujaa_manager"
    assert audit.resource_type == "task"
    assert audit.resource_id == task.task_id
    assert audit.operation_id == cancel_operation_id
    assert audit.outcome == "accepted"
    assert audit.reason_code == "cancel_applied"
    assert audit.event_id == (
        "event-execution-transition-"
        f"{execution.execution_id}:cancelled"
    )
    rendered = repr(audit)
    assert "sensitive command" not in rendered
    assert "sensitive source error" not in rendered


def test_late_cancel_audits_preserved_terminal_winner():
    audit_store = InMemoryAuditStore()
    manager = _manager(audit_store=audit_store)
    task, execution = _seed_source(
        manager,
        "cancel-audit-late",
        status=ExecutionStatus.COMPLETED,
    )

    response = manager.cancel_task(
        task.task_id,
        cancel_operation_id="op-cancel-request-late",
        cleanup_operation_id="op-cancel-cleanup-late",
    )

    assert response["status"] == "completed"
    assert manager.execution_registry.get(
        execution.execution_id
    ).status == ExecutionStatus.COMPLETED
    audit = _audit(
        audit_store,
        response["audit_append_receipt"].record_id,
    )
    assert audit.outcome == "rejected"
    assert audit.reason_code == "terminal_winner_preserved"


@pytest.mark.parametrize(
    ("case", "reason_code"),
    (
        ("task_missing", "task_not_found"),
        ("execution_missing", "execution_not_found"),
    ),
)
def test_cancel_pretransition_rejection_is_structured(
    case,
    reason_code,
):
    audit_store = InMemoryAuditStore()
    manager = _manager(audit_store=audit_store)
    task_id = f"task-cancel-{case}"

    if case == "execution_missing":
        manager.task_store.create(
            TaskRecord(
                task_id=task_id,
                work_id=f"work-cancel-{case}",
                command="sensitive missing execution command",
                status="queued",
            )
        )

    with pytest.raises(ValueError) as caught:
        manager.cancel_task(
            task_id,
            cancel_operation_id=f"op-cancel-{case}",
            cleanup_operation_id=f"op-cleanup-{case}",
        )

    error = caught.value
    assert type(error).__name__ == "AuditedCancelError"
    assert error.reason_code == reason_code
    assert error.audit_append_receipt.result == (
        AppendResult.APPENDED
    )
    audit = _audit(
        audit_store,
        error.audit_append_receipt.record_id,
    )
    assert audit.outcome == "rejected"
    assert audit.reason_code == reason_code
    assert audit.event_id is None
    assert "sensitive" not in repr(audit)


def test_cancel_audit_write_failure_preserves_cancel_and_cleanup():
    manager = _manager(audit_store=FailingAuditStore())
    task, execution = _seed_source(
        manager,
        "cancel-audit-failure",
        status=ExecutionStatus.QUEUED,
    )

    response = manager.cancel_task(
        task.task_id,
        cancel_operation_id="op-cancel-request-failure",
        cleanup_operation_id="op-cancel-cleanup-failure",
    )

    assert response["status"] == "cancelled"
    assert response["cleanup_disposition"] == "not_owned"
    assert response["audit_append_receipt"].result == (
        AppendResult.WRITE_FAILED
    )
    assert manager.execution_registry.get(
        execution.execution_id
    ).status == ExecutionStatus.CANCELLED


def test_cancel_api_passes_separate_request_and_cleanup_ids(
    monkeypatch,
):
    captured = {}

    class FakeManager:
        def cancel_task(
            self,
            task_id,
            *,
            cancel_operation_id,
            cleanup_operation_id,
        ):
            captured["task_id"] = task_id
            captured["cancel_operation_id"] = cancel_operation_id
            captured["cleanup_operation_id"] = cleanup_operation_id
            return {
                "task_id": task_id,
                "status": "cancelled",
            }

    import apps.api.app as api_module

    monkeypatch.setattr(api_module, "manager", FakeManager())
    client = api_module.app.test_client()
    api_key = __import__("os").getenv("SHUJAA_API_KEY")

    response = client.post(
        "/tasks/task-audit-cancel-api/cancel",
        headers={"X-Shujaa-Key": api_key},
    )

    assert response.status_code == 200
    assert captured["task_id"] == "task-audit-cancel-api"
    assert captured["cancel_operation_id"].startswith(
        "op-cancel-request-"
    )
    assert captured["cleanup_operation_id"].startswith(
        "op-cancel-cleanup-"
    )
    assert captured["cancel_operation_id"] != (
        captured["cleanup_operation_id"]
    )
