from __future__ import annotations

from dataclasses import fields

import pytest

import core.manager.service as service_module
from core.manager.service import ShujaaManager
from core.policy.contracts import (
    ActorRef,
    AuthorizationContext,
    AuthorizationRequest,
    ResourceRef,
)
from core.policy.evaluator import SinglePrincipalCancelEvaluator
from core.runtime.process_registry import ProcessRegistry
from core.runtime.owned_local_process_termination_contract import (
    OwnedLocalProcessTerminationDisposition,
    OwnedLocalProcessTerminationResult,
)
from core.runtime.process_registry_contract import (
    CleanupDisposition,
    CleanupResult,
    ProcessOwnership,
)
from core.tasks.store import TaskRecord
from core.work.event_store import InMemoryEventStore
from core.work.events import AppendResult
from core.work.models import Execution, ExecutionStatus


class UnusedRunner:
    def start(self, command):
        raise AssertionError("Runner must not be called.")


class TerminationAdapterFake:
    def __init__(self):
        self.commands = []

    def terminate(self, command):
        self.commands.append(command)
        return OwnedLocalProcessTerminationResult(
            disposition=(
                OwnedLocalProcessTerminationDisposition
                .GRACEFUL_TERMINATION
            )
        )


_CANCEL_ACTOR = ActorRef(
    actor_type="service",
    actor_id="test-cleanup-contract-local-api",
)


def _authorized_cancel(
    manager,
    task_id,
    *,
    cancel_operation_id,
    cleanup_operation_id,
):
    manager.cancel_authorization_evaluator = (
        SinglePrincipalCancelEvaluator(
            principal=_CANCEL_ACTOR,
            policy_version="test-cleanup-contract-v1",
        )
    )
    return manager.cancel_task(
        task_id,
        authorization_request=AuthorizationRequest(
            actor=_CANCEL_ACTOR,
            action="task.cancel",
            resource=ResourceRef(
                resource_type="task",
                resource_id=task_id,
            ),
            context=AuthorizationContext(
                request_id=f"request-{cancel_operation_id}",
                operation_id=cancel_operation_id,
            ),
        ),
        cancel_operation_id=cancel_operation_id,
        cleanup_operation_id=cleanup_operation_id,
    )


def _ownership(
    task_id: str,
    *,
    execution_id: str = "exec-cleanup-contract",
    pid: int = 7101,
    pgid: int = 7201,
    start_ticks: int = 7301,
) -> ProcessOwnership:
    return ProcessOwnership(
        task_id=task_id,
        execution_id=execution_id,
        pid=pid,
        pgid=pgid,
        process_start_time_ticks=start_ticks,
    )


def _seed_running_owner(
    manager: ShujaaManager,
    registry: ProcessRegistry,
    *,
    task_id: str,
    execution_id: str,
    work_id: str,
) -> ProcessOwnership:
    manager.task_store.create(
        TaskRecord(
            task_id=task_id,
            work_id=work_id,
            command="sensitive cleanup contract command",
            status="running",
            process_id=7101,
            process_group_id=7201,
        )
    )
    manager.execution_registry.create(
        Execution(
            execution_id=execution_id,
            work_id=work_id,
            task_id=task_id,
        )
    )
    manager._transition_execution(
        execution_id,
        target_status=ExecutionStatus.RUNNING,
        operation_id=f"{execution_id}:running",
    )
    owner = _ownership(
        task_id,
        execution_id=execution_id,
    )
    registry.register(owner)
    return owner


def test_cleanup_event_outcome_is_manager_contract_only():
    outcome_type = getattr(
        service_module,
        "CleanupEventOutcome",
        None,
    )

    assert outcome_type is not None
    assert [item.name for item in fields(outcome_type)] == [
        "cleanup_result",
        "event_append_receipt",
    ]
    assert "event_append_receipt" not in {
        item.name for item in fields(CleanupResult)
    }


@pytest.mark.parametrize(
    ("disposition", "ownership_retained"),
    (
        (CleanupDisposition.TERMINATED_AND_RELEASED, False),
        (CleanupDisposition.ALREADY_EXITED_AND_RELEASED, False),
        (CleanupDisposition.NOT_OWNED, False),
        (CleanupDisposition.OWNER_MISMATCH, True),
        (CleanupDisposition.IDENTITY_MISMATCH, True),
        (CleanupDisposition.PROCESS_GROUP_MISMATCH, True),
        (CleanupDisposition.IDENTITY_CHECK_FAILED_RETAINED, True),
        (CleanupDisposition.TERMINATION_FAILED_RETAINED, True),
    ),
)
def test_cleanup_event_matches_canonical_contract_for_all_dispositions(
    disposition,
    ownership_retained,
):
    store = InMemoryEventStore()
    manager = ShujaaManager(
        crew_runner=UnusedRunner(),
        event_store=store,
    )
    task_id = f"task-contract-{disposition.value}"
    operation_id = f"op-contract-{disposition.value}"
    work_id = f"work-contract-{disposition.value}"
    owner = (
        None
        if disposition is CleanupDisposition.NOT_OWNED
        else _ownership(task_id)
    )
    result = CleanupResult(
        disposition=disposition,
        ownership=owner,
        error=(
            "sensitive raw cleanup error"
            if disposition
            in {
                CleanupDisposition.IDENTITY_CHECK_FAILED_RETAINED,
                CleanupDisposition.TERMINATION_FAILED_RETAINED,
            }
            else None
        ),
    )

    receipt = manager._append_cleanup_event(
        result,
        task_id=task_id,
        cleanup_operation_id=operation_id,
        trigger="registered_cleanup",
        work_id=work_id,
    )

    assert receipt.result is AppendResult.APPENDED
    event = store.get(receipt.record_id).record
    assert event.event_type == (
        "process_ownership.cleanup."
        f"{disposition.value}"
    )
    assert event.entity_type == "process_ownership"
    assert event.entity_id == task_id
    assert event.source_component == "core.manager.cleanup"
    assert event.operation_id == operation_id
    assert event.task_id == task_id
    assert event.work_id == work_id
    assert event.payload == {
        "disposition": disposition.value,
        "ownership_retained": ownership_retained,
        "trigger": "registered_cleanup",
    }
    rendered = repr(event.payload)
    assert "sensitive raw cleanup error" not in rendered
    assert "7101" not in rendered
    assert "7201" not in rendered
    assert "7301" not in rendered


def test_cancel_exposes_cleanup_event_receipt_and_cancel_trigger(
    tmp_path,
):
    registry = ProcessRegistry(tmp_path / "processes.json")
    store = InMemoryEventStore()
    adapter = TerminationAdapterFake()
    manager = ShujaaManager(
        crew_runner=UnusedRunner(),
        process_registry=registry,
        event_store=store,
        owned_local_process_termination_adapter=adapter,
    )
    task_id = "task-cancel-cleanup-contract"
    execution_id = "exec-cancel-cleanup-contract"
    work_id = "work-cancel-cleanup-contract"
    cleanup_operation_id = "op-cancel-cleanup-contract"
    _seed_running_owner(
        manager,
        registry,
        task_id=task_id,
        execution_id=execution_id,
        work_id=work_id,
    )
    response = _authorized_cancel(
        manager,
        task_id,
        cancel_operation_id="op-cancel-request-contract",
        cleanup_operation_id=cleanup_operation_id,
    )

    receipt = response["cleanup_event_append_receipt"]
    assert receipt.result is AppendResult.APPENDED
    event = store.get(receipt.record_id).record
    assert event.payload["trigger"] == "cancel"
    assert event.work_id == work_id
    assert response["cleanup_disposition"] == (
        CleanupDisposition.TERMINATED_AND_RELEASED.value
    )
    assert len(adapter.commands) == 1


def test_registered_cleanup_returns_compatible_outcome_per_task(
    tmp_path,
    monkeypatch,
):
    registry = ProcessRegistry(tmp_path / "processes.json")
    manager = ShujaaManager(
        crew_runner=UnusedRunner(),
        process_registry=registry,
    )
    task_id = "task-bulk-cleanup-contract"
    execution_id = "exec-bulk-cleanup-contract"
    work_id = "work-bulk-cleanup-contract"
    _seed_running_owner(
        manager,
        registry,
        task_id=task_id,
        execution_id=execution_id,
        work_id=work_id,
    )
    manager._read_process_start_time_ticks = lambda pid: 7301
    monkeypatch.setattr(
        service_module.os,
        "getpgid",
        lambda pid: 7201,
    )
    manager._terminate_process_group_by_id = lambda pgid: None

    results = manager.cleanup_registered_processes(
        cleanup_operation_id="op-bulk-cleanup-contract",
    )

    outcome = results[task_id]
    assert type(outcome).__name__ == "CleanupAuditOutcome"
    assert type(
        outcome.cleanup_event_outcome
    ).__name__ == "CleanupEventOutcome"
    assert outcome.cleanup_result.disposition is (
        CleanupDisposition.TERMINATED_AND_RELEASED
    )
    assert outcome.event_append_receipt.result is (
        AppendResult.APPENDED
    )
    assert outcome.audit_append_receipt.result is (
        AppendResult.APPENDED
    )
    assert outcome.disposition is outcome.cleanup_result.disposition
    assert outcome.ownership is outcome.cleanup_result.ownership
    assert outcome.error is outcome.cleanup_result.error
    event = manager.event_store.get(
        outcome.event_append_receipt.record_id
    ).record
    assert event.payload["trigger"] == "registered_cleanup"
    assert event.work_id == work_id


def test_cleanup_event_write_failure_is_visible_and_non_blocking(
    tmp_path,
    monkeypatch,
):
    registry = ProcessRegistry(tmp_path / "processes.json")
    manager = ShujaaManager(
        crew_runner=UnusedRunner(),
        process_registry=registry,
    )
    task_id = "task-cleanup-write-failure-contract"
    execution_id = "exec-cleanup-write-failure-contract"
    work_id = "work-cleanup-write-failure-contract"
    _seed_running_owner(
        manager,
        registry,
        task_id=task_id,
        execution_id=execution_id,
        work_id=work_id,
    )
    manager._read_process_start_time_ticks = lambda pid: 7301
    monkeypatch.setattr(
        service_module.os,
        "getpgid",
        lambda pid: 7201,
    )
    manager._terminate_process_group_by_id = lambda pgid: None
    manager.event_store = InMemoryEventStore(
        integrity_hasher=lambda data: (_ for _ in ()).throw(
            OSError("simulated cleanup event write failure")
        )
    )

    results = manager.cleanup_registered_processes(
        cleanup_operation_id="op-cleanup-write-failure-contract",
    )

    outcome = results[task_id]
    assert outcome.cleanup_result.disposition is (
        CleanupDisposition.TERMINATED_AND_RELEASED
    )
    assert outcome.event_append_receipt.result is (
        AppendResult.WRITE_FAILED
    )
    assert outcome.event_append_receipt.error_code == "OSError"
    assert registry.get(task_id) is None
    assert manager.execution_registry.get(
        execution_id
    ).status is ExecutionStatus.RUNNING
