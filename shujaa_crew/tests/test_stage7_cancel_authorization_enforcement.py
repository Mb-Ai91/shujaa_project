from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields
from hashlib import sha256
import importlib
import inspect
from pathlib import Path

import pytest

from core.manager.service import ShujaaManager
from core.tasks.store import TaskRecord
from core.work.event_store import (
    AppendReceipt,
    InMemoryAuditStore,
    InMemoryEventStore,
)
from core.work.events import AppendResult
from core.work.models import Execution, ExecutionStatus


_UNSET = object()
_API_ACTOR_ID = "local-api-service-principal"
_POLICY_VERSION = "stage7.1-test-policy-v1"


class _UnusedRunner:
    def start(self, command):
        raise AssertionError("Runtime execution is not expected.")


class _Evaluator:
    def __init__(self, decision=None, error=None):
        self.decision = decision
        self.error = error
        self.requests = []

    def evaluate(self, request):
        self.requests.append(request)
        if self.error is not None:
            raise self.error
        return self.decision


class _RecordingAuditStore:
    def __init__(
        self,
        *,
        fail_when=None,
        raise_when=None,
        malformed_when=None,
        trace=None,
    ):
        self._delegate = InMemoryAuditStore()
        self.fail_when = fail_when
        self.raise_when = raise_when
        self.malformed_when = malformed_when
        self.trace = trace
        self.records = []

    def _append(self, record, *, replay_stable):
        self.records.append(record)
        if self.trace is not None:
            self.trace.append("audit")
        if self.raise_when is not None and self.raise_when(record):
            raise RuntimeError("injected_stage7_audit_exception")
        if (
            self.malformed_when is not None
            and self.malformed_when(record)
        ):
            return object()
        if self.fail_when is not None and self.fail_when(record):
            return AppendReceipt(
                result=AppendResult.WRITE_FAILED,
                record_id=record.audit_id,
                error_code="injected_stage7_audit_failure",
            )
        if replay_stable:
            return self._delegate.append_replay_stable(record)
        return self._delegate.append(record)

    def append(self, record):
        return self._append(record, replay_stable=False)

    def append_replay_stable(self, record):
        return self._append(record, replay_stable=True)

    def verify_integrity(self):
        return self._delegate.verify_integrity()

    def get(self, record_id):
        return self._delegate.get(record_id)

    def list(self, after_sequence=0, limit=None):
        return self._delegate.list(after_sequence, limit)


def _contracts():
    return importlib.import_module("core.policy.contracts")


def _actor(contracts):
    return contracts.ActorRef(
        actor_type="service",
        actor_id=_API_ACTOR_ID,
    )


def _request(
    contracts,
    task_id,
    *,
    action="task.cancel",
    operation_id="op-stage7-cancel",
):
    return contracts.AuthorizationRequest(
        actor=_actor(contracts),
        action=action,
        resource=contracts.ResourceRef(
            resource_type="task",
            resource_id=task_id,
        ),
        context=contracts.AuthorizationContext(
            request_id=f"request-{operation_id}",
            operation_id=operation_id,
        ),
    )


def _decision(contracts, effect):
    return contracts.AuthorizationDecision(
        effect=effect,
        reason_code=(
            "cancel_allowed"
            if effect == "ALLOW"
            else "cancel_denied"
        ),
        policy_version=_POLICY_VERSION,
    )


def _manager(*, evaluator=_UNSET, audit_store=None):
    kwargs = {
        "crew_runner": _UnusedRunner(),
        "audit_store": audit_store or InMemoryAuditStore(),
        "event_store": InMemoryEventStore(),
    }
    if evaluator is not _UNSET:
        kwargs["cancel_authorization_evaluator"] = evaluator
    return ShujaaManager(**kwargs)


def _seed(manager, suffix, *, status=ExecutionStatus.QUEUED):
    task_id = f"task-stage7-{suffix}"
    execution_id = f"exec-stage7-{suffix}"
    work_id = f"work-stage7-{suffix}"
    terminal_operation_id = None
    state_version = 0
    if status in {
        ExecutionStatus.COMPLETED,
        ExecutionStatus.FAILED,
        ExecutionStatus.TIMED_OUT,
        ExecutionStatus.CANCELLED,
    }:
        state_version = 1
        terminal_operation_id = (
            f"{execution_id}:cancelled"
            if status is ExecutionStatus.CANCELLED
            else f"{execution_id}:{status.value}"
        )
    manager.task_store.create(
        TaskRecord(
            task_id=task_id,
            work_id=work_id,
            command="raw-command secret-api-key must never enter audit",
            status=status.value,
        )
    )
    manager.execution_registry.create(
        Execution(
            execution_id=execution_id,
            work_id=work_id,
            task_id=task_id,
            status=status,
            state_version=state_version,
            terminal_operation_id=terminal_operation_id,
        )
    )
    return task_id, execution_id


def _cancel(manager, contracts, task_id, *, request=None):
    operation_id = "op-stage7-cancel"
    return manager.cancel_task(
        task_id,
        authorization_request=(
            request
            if request is not None
            else _request(
                contracts,
                task_id,
                operation_id=operation_id,
            )
        ),
        cancel_operation_id=operation_id,
        cleanup_operation_id="op-stage7-cleanup",
    )


def _failure_code(outcome):
    if isinstance(outcome, dict):
        return (
            outcome.get("error_code")
            or outcome.get("reason_code")
            or outcome.get("warning_code")
        )
    return (
        getattr(outcome, "error_code", None)
        or getattr(outcome, "reason_code", None)
        or getattr(outcome, "warning_code", None)
    )


def _invoke(manager, contracts, task_id, *, request=None):
    try:
        return _cancel(
            manager,
            contracts,
            task_id,
            request=request,
        )
    except Exception as error:
        return error


def test_authorization_contracts_are_immutable_and_shujaa_owned():
    contracts = _contracts()
    actor = _actor(contracts)
    resource = contracts.ResourceRef(
        resource_type="task",
        resource_id="task-contract",
    )
    context = contracts.AuthorizationContext(
        request_id="request-contract",
        operation_id="operation-contract",
    )
    request = contracts.AuthorizationRequest(
        actor=actor,
        action="task.cancel",
        resource=resource,
        context=context,
    )
    decision = _decision(contracts, "ALLOW")

    for contract in (actor, resource, context, request, decision):
        field_name = fields(contract)[0].name
        with pytest.raises(FrozenInstanceError):
            setattr(contract, field_name, "changed")

    assert hasattr(
        contracts.CancelAuthorizationEvaluatorProtocol,
        "evaluate",
    )


@pytest.mark.parametrize(
    "factory",
    (
        lambda contracts: contracts.ActorRef(
            actor_type="",
            actor_id=_API_ACTOR_ID,
        ),
        lambda contracts: contracts.ActorRef(
            actor_type="service",
            actor_id=" ",
        ),
        lambda contracts: contracts.ResourceRef(
            resource_type="",
            resource_id="task-1",
        ),
        lambda contracts: contracts.ResourceRef(
            resource_type="task",
            resource_id=" ",
        ),
        lambda contracts: contracts.AuthorizationContext(
            request_id="",
            operation_id="operation-1",
        ),
        lambda contracts: contracts.AuthorizationContext(
            request_id="request-1",
            operation_id=" ",
        ),
    ),
)
def test_authorization_contracts_reject_empty_identity(factory):
    contracts = _contracts()
    with pytest.raises((TypeError, ValueError)):
        factory(contracts)


def test_authorization_decision_rejects_unknown_effect():
    contracts = _contracts()
    with pytest.raises((TypeError, ValueError)):
        _decision(contracts, "UNKNOWN")


def test_authorization_contracts_expose_only_minimal_fields():
    contracts = _contracts()
    assert {field.name for field in fields(contracts.ActorRef)} == {
        "actor_type",
        "actor_id",
    }
    assert {field.name for field in fields(contracts.ResourceRef)} == {
        "resource_type",
        "resource_id",
    }
    assert {
        field.name
        for field in fields(contracts.AuthorizationContext)
    } == {"request_id", "operation_id"}
    assert {
        field.name
        for field in fields(contracts.AuthorizationRequest)
    } == {"actor", "action", "resource", "context"}
    assert {
        field.name
        for field in fields(contracts.AuthorizationDecision)
    } == {"effect", "reason_code", "policy_version"}


@pytest.mark.parametrize(
    "mode",
    ("missing", "exception", "malformed"),
)
def test_unavailable_evaluator_fails_closed_without_side_effects(mode):
    contracts = _contracts()
    if mode == "missing":
        manager = _manager()
    elif mode == "exception":
        manager = _manager(
            evaluator=_Evaluator(error=RuntimeError("unavailable"))
        )
    else:
        manager = _manager(evaluator=_Evaluator(decision=object()))

    task_id, execution_id = _seed(manager, mode)
    cleanup_calls = []
    manager._cleanup_process_ownership = (
        lambda *args, **kwargs: cleanup_calls.append(task_id)
    )

    outcome = _invoke(manager, contracts, task_id)

    assert _failure_code(outcome) == "EVALUATOR_UNAVAILABLE"
    assert manager.execution_registry.get(execution_id).status is (
        ExecutionStatus.QUEUED
    )
    assert manager.task_store.get(task_id).status == "queued"
    assert cleanup_calls == []


def test_policy_deny_fails_closed_without_mutation_or_cleanup():
    contracts = _contracts()
    manager = _manager(
        evaluator=_Evaluator(_decision(contracts, "DENY"))
    )
    task_id, execution_id = _seed(manager, "deny")
    cleanup_calls = []
    manager._cleanup_process_ownership = (
        lambda *args, **kwargs: cleanup_calls.append(task_id)
    )

    outcome = _invoke(manager, contracts, task_id)

    assert _failure_code(outcome) == "POLICY_DENIED"
    assert manager.execution_registry.get(execution_id).status is (
        ExecutionStatus.QUEUED
    )
    assert cleanup_calls == []


def test_pre_action_evidence_failure_blocks_cancel_and_cleanup():
    contracts = _contracts()
    audit_store = _RecordingAuditStore(fail_when=lambda record: True)
    manager = _manager(
        evaluator=_Evaluator(_decision(contracts, "ALLOW")),
        audit_store=audit_store,
    )
    task_id, execution_id = _seed(manager, "pre-audit-failure")
    cleanup_calls = []
    manager._cleanup_process_ownership = (
        lambda *args, **kwargs: cleanup_calls.append(task_id)
    )

    outcome = _invoke(manager, contracts, task_id)

    assert _failure_code(outcome) == "AUDIT_UNAVAILABLE"
    assert manager.execution_registry.get(execution_id).status is (
        ExecutionStatus.QUEUED
    )
    assert cleanup_calls == []


def test_pre_action_audit_exception_fails_closed():
    contracts = _contracts()
    audit_store = _RecordingAuditStore(raise_when=lambda record: True)
    manager = _manager(
        evaluator=_Evaluator(_decision(contracts, "ALLOW")),
        audit_store=audit_store,
    )
    task_id, execution_id = _seed(manager, "pre-audit-exception")
    cleanup_calls = []
    manager._cleanup_process_ownership = (
        lambda *args, **kwargs: cleanup_calls.append(task_id)
    )

    outcome = _invoke(manager, contracts, task_id)

    assert _failure_code(outcome) == "AUDIT_UNAVAILABLE"
    assert _failure_code(outcome) != "POLICY_DENIED"
    assert manager.execution_registry.get(execution_id).status is (
        ExecutionStatus.QUEUED
    )
    assert manager.task_store.get(task_id).status == "queued"
    assert cleanup_calls == []


def test_pre_action_malformed_receipt_fails_closed():
    contracts = _contracts()
    audit_store = _RecordingAuditStore(
        malformed_when=lambda record: True
    )
    manager = _manager(
        evaluator=_Evaluator(_decision(contracts, "ALLOW")),
        audit_store=audit_store,
    )
    task_id, execution_id = _seed(manager, "pre-audit-malformed")
    cleanup_calls = []
    manager._cleanup_process_ownership = (
        lambda *args, **kwargs: cleanup_calls.append(task_id)
    )

    outcome = _invoke(manager, contracts, task_id)

    assert _failure_code(outcome) == "AUDIT_UNAVAILABLE"
    assert manager.execution_registry.get(execution_id).status is (
        ExecutionStatus.QUEUED
    )
    assert manager.task_store.get(task_id).status == "queued"
    assert cleanup_calls == []


def test_authorization_evidence_precedes_lifecycle_transition():
    contracts = _contracts()
    trace = []
    audit_store = _RecordingAuditStore(trace=trace)
    manager = _manager(
        evaluator=_Evaluator(_decision(contracts, "ALLOW")),
        audit_store=audit_store,
    )
    task_id, _ = _seed(manager, "ordering")
    original = manager._reconcile_terminal_execution

    def tracked_transition(*args, **kwargs):
        trace.append("transition")
        return original(*args, **kwargs)

    manager._reconcile_terminal_execution = tracked_transition

    _cancel(manager, contracts, task_id)

    assert trace[0] == "audit"
    assert trace.index("audit") < trace.index("transition")
    task_audits = [
        record
        for record in audit_store.records
        if record.resource_type == "task"
    ]
    assert len(task_audits) >= 2
    assert task_audits[0].audit_id != task_audits[-1].audit_id


@pytest.mark.parametrize(
    ("initial_status", "expected_status"),
    (
        (ExecutionStatus.QUEUED, ExecutionStatus.CANCELLED),
        (ExecutionStatus.CANCELLED, ExecutionStatus.CANCELLED),
        (ExecutionStatus.COMPLETED, ExecutionStatus.COMPLETED),
    ),
)
def test_allow_preserves_applied_replay_and_terminal_winner(
    initial_status,
    expected_status,
):
    contracts = _contracts()
    manager = _manager(
        evaluator=_Evaluator(_decision(contracts, "ALLOW"))
    )
    task_id, execution_id = _seed(
        manager,
        initial_status.value,
        status=initial_status,
    )

    response = _cancel(manager, contracts, task_id)

    assert manager.execution_registry.get(execution_id).status is (
        expected_status
    )
    assert response["status"] == expected_status.value


def test_post_action_audit_failure_preserves_action_and_stage5_winner():
    contracts = _contracts()

    def fail_outcome(record):
        return (
            record.resource_type == "task"
            and record.event_id is not None
        )

    audit_store = _RecordingAuditStore(fail_when=fail_outcome)
    manager = _manager(
        evaluator=_Evaluator(_decision(contracts, "ALLOW")),
        audit_store=audit_store,
    )
    task_id, execution_id = _seed(manager, "post-audit-failure")

    response = _cancel(manager, contracts, task_id)

    assert response["status"] == "cancelled"
    assert response["audit_status"] == "FAILED"
    assert response["warning_code"] == "POST_ACTION_AUDIT_FAILED"
    assert manager.execution_registry.get(execution_id).status is (
        ExecutionStatus.CANCELLED
    )
    assert manager.task_store.get(task_id).status == "cancelled"


def test_post_action_audit_exception_preserves_result_and_winner(
    monkeypatch,
    caplog,
):
    contracts = _contracts()
    api_key = "stage7-api-key-diagnostic-test-only"
    sensitive_exception_message = (
        "sensitive-audit-backend-message-must-not-be-logged"
    )
    raw_payload = "raw-cancel-payload-must-not-be-logged"
    monkeypatch.setenv("SHUJAA_API_KEY", api_key)

    def is_outcome_audit(record):
        is_outcome = (
            record.resource_type == "task"
            and record.event_id is not None
        )
        if is_outcome:
            raise RuntimeError(sensitive_exception_message)
        return False

    audit_store = _RecordingAuditStore(raise_when=is_outcome_audit)
    manager = _manager(
        evaluator=_Evaluator(_decision(contracts, "ALLOW")),
        audit_store=audit_store,
    )
    task_id, execution_id = _seed(manager, "post-audit-exception")
    reconciliation_calls = []
    original = manager._reconcile_terminal_execution

    def tracked_transition(*args, **kwargs):
        reconciliation_calls.append(args[1])
        return original(*args, **kwargs)

    manager._reconcile_terminal_execution = tracked_transition
    import apps.api.app as api_module

    monkeypatch.setattr(api_module, "manager", manager)
    client = api_module.app.test_client()
    with caplog.at_level(
        "WARNING",
        logger="core.manager.service",
    ):
        api_response = client.post(
            f"/tasks/{task_id}/cancel",
            headers={"X-Shujaa-Key": api_key},
            json={"payload": raw_payload},
        )

    assert api_response.status_code == 200
    response = api_response.get_json()
    assert response["status"] == "cancelled"
    assert response["action_occurred"] is True
    assert response["audit_status"] == "FAILED"
    assert response["warning_code"] == "POST_ACTION_AUDIT_FAILED"
    assert response["cleanup_disposition"] == "not_owned"
    assert manager.execution_registry.get(execution_id).status is (
        ExecutionStatus.CANCELLED
    )
    assert manager.task_store.get(task_id).status == "cancelled"
    assert reconciliation_calls == [execution_id]

    diagnostics = [
        record
        for record in caplog.records
        if (
            record.name == "core.manager.service"
            and record.getMessage() == "post_action_audit_failed"
        )
    ]
    assert len(diagnostics) == 1
    diagnostic = diagnostics[0]
    assert diagnostic.levelname == "WARNING"
    assert diagnostic.diagnostic_code == (
        "POST_ACTION_AUDIT_FAILED"
    )
    assert diagnostic.exception_type == "RuntimeError"
    assert diagnostic.operation_id.startswith("op-cancel-request-")
    assert diagnostic.request_id.startswith("request-cancel-")
    assert diagnostic.resource_type == "task"
    assert diagnostic.resource_id == task_id
    assert diagnostic.args == ()
    assert diagnostic.exc_info is None
    assert diagnostic.exc_text is None
    assert diagnostic.stack_info is None

    forbidden_values = (
        sensitive_exception_message,
        api_key,
        "X-Shujaa-Key",
        raw_payload,
        "raw-command",
        "secret-api-key",
    )
    for record in caplog.records:
        rendered_record = repr(record.__dict__)
        rendered_message = record.getMessage()
        rendered_args = repr(record.args)
        for forbidden in forbidden_values:
            assert forbidden not in rendered_record
            assert forbidden not in rendered_message
            assert forbidden not in rendered_args

    external_response = api_response.get_data(as_text=True)
    assert sensitive_exception_message not in external_response
    assert "RuntimeError" not in external_response
    assert "post_action_audit_failed" not in external_response
    assert "diagnostic_code" not in external_response
    assert diagnostic.operation_id not in external_response
    assert diagnostic.request_id not in external_response


def test_post_action_malformed_receipt_preserves_result_and_winner():
    contracts = _contracts()

    def is_outcome_audit(record):
        return (
            record.resource_type == "task"
            and record.event_id is not None
        )

    audit_store = _RecordingAuditStore(malformed_when=is_outcome_audit)
    manager = _manager(
        evaluator=_Evaluator(_decision(contracts, "ALLOW")),
        audit_store=audit_store,
    )
    task_id, execution_id = _seed(manager, "post-audit-malformed")

    response = _cancel(manager, contracts, task_id)

    assert response["status"] == "cancelled"
    assert response["action_occurred"] is True
    assert response["audit_status"] == "FAILED"
    assert response["warning_code"] == "POST_ACTION_AUDIT_FAILED"
    assert response["cleanup_disposition"] == "not_owned"
    assert manager.execution_registry.get(execution_id).status is (
        ExecutionStatus.CANCELLED
    )
    assert manager.task_store.get(task_id).status == "cancelled"


@pytest.mark.parametrize(
    ("action", "resource_suffix"),
    (
        ("execution.retry", "bound"),
        ("task.cancel", "other"),
    ),
)
def test_allow_cannot_cross_action_or_resource(action, resource_suffix):
    contracts = _contracts()
    manager = _manager(
        evaluator=_Evaluator(_decision(contracts, "ALLOW"))
    )
    task_id, execution_id = _seed(manager, "scope-bound")
    request = _request(
        contracts,
        (
            task_id
            if resource_suffix == "bound"
            else f"{task_id}-other"
        ),
        action=action,
    )

    outcome = _invoke(
        manager,
        contracts,
        task_id,
        request=request,
    )

    assert _failure_code(outcome) in {
        "POLICY_DENIED",
        "EVALUATOR_UNAVAILABLE",
    }
    assert manager.execution_registry.get(execution_id).status is (
        ExecutionStatus.QUEUED
    )


def test_authorization_and_audit_exclude_key_secret_and_raw_command():
    contracts = _contracts()
    audit_store = _RecordingAuditStore()
    manager = _manager(
        evaluator=_Evaluator(_decision(contracts, "ALLOW")),
        audit_store=audit_store,
    )
    task_id, _ = _seed(manager, "privacy")
    request = _request(contracts, task_id)

    _cancel(manager, contracts, task_id, request=request)

    rendered = repr((request, audit_store.records))
    assert "secret-api-key" not in rendered
    assert "raw-command" not in rendered
    assert "authorization" not in {
        field.name.casefold()
        for contract in (
            request.actor,
            request.resource,
            request.context,
            request,
        )
        for field in fields(contract)
    }


def test_api_post_action_audit_exception_preserves_cancel_status(
    monkeypatch,
):
    contracts = _contracts()
    api_key = "stage7-api-key-post-audit-test-only"
    monkeypatch.setenv("SHUJAA_API_KEY", api_key)
    import apps.api.app as api_module

    def is_outcome_audit(record):
        return (
            record.resource_type == "task"
            and record.event_id is not None
        )

    audit_store = _RecordingAuditStore(raise_when=is_outcome_audit)
    manager = _manager(
        evaluator=_Evaluator(_decision(contracts, "ALLOW")),
        audit_store=audit_store,
    )
    task_id, execution_id = _seed(manager, "api-post-audit-exception")
    monkeypatch.setattr(api_module, "manager", manager)
    client = api_module.app.test_client()

    response = client.post(
        f"/tasks/{task_id}/cancel",
        headers={"X-Shujaa-Key": api_key},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "cancelled"
    assert payload["action_occurred"] is True
    assert payload["audit_status"] == "FAILED"
    assert payload["warning_code"] == "POST_ACTION_AUDIT_FAILED"
    assert api_key not in response.get_data(as_text=True)
    assert manager.execution_registry.get(execution_id).status is (
        ExecutionStatus.CANCELLED
    )


def test_api_maps_authenticated_channel_to_stable_opaque_service_actor(
    monkeypatch,
):
    api_key = "stage7-api-key-must-not-be-an-actor"
    monkeypatch.setenv("SHUJAA_API_KEY", api_key)
    import apps.api.app as api_module

    captured = []

    class FakeManager:
        def cancel_task(self, task_id, **kwargs):
            captured.append(kwargs)
            return {"task_id": task_id, "status": "cancelled"}

    monkeypatch.setattr(api_module, "manager", FakeManager())
    client = api_module.app.test_client()

    for _ in range(2):
        response = client.post(
            "/tasks/task-stage7-api/cancel",
            headers={"X-Shujaa-Key": api_key},
        )
        assert response.status_code == 200

    assert all("authorization_request" in item for item in captured)
    actors = [item["authorization_request"].actor for item in captured]
    assert actors[0] == actors[1]
    assert actors[0].actor_type == "service"
    assert actors[0].actor_id
    assert actors[0].actor_id not in {
        api_key,
        sha256(api_key.encode("utf-8")).hexdigest(),
    }
    assert "user" not in actors[0].actor_type.casefold()
    assert "human" not in actors[0].actor_type.casefold()


def test_manager_command_entry_owns_cancel_enforcement():
    init_signature = inspect.signature(ShujaaManager)
    cancel_signature = inspect.signature(ShujaaManager.cancel_task)
    source = inspect.getsource(ShujaaManager.cancel_task)

    assert "cancel_authorization_evaluator" in init_signature.parameters
    assert "authorization_request" in cancel_signature.parameters
    assert "evaluate" in source
    assert "EVALUATOR_UNAVAILABLE" in source
    assert "POLICY_DENIED" in source


def test_runtime_cancel_call_sites_do_not_bypass_manager_command():
    package_root = Path(__file__).resolve().parents[1]
    call_sites = []
    for base in (package_root / "core", package_root / "apps"):
        for path in base.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "cancel_task"
                ):
                    call_sites.append(path.relative_to(package_root).as_posix())

    assert call_sites == ["apps/api/app.py"]

    manager_source = ast.parse(
        inspect.getsource(importlib.import_module("core.manager.service"))
    )
    manager_class = next(
        node
        for node in manager_source.body
        if isinstance(node, ast.ClassDef)
        and node.name == "ShujaaManager"
    )
    cancel_methods = []
    for method in manager_class.body:
        if not isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for node in ast.walk(method):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "_reconcile_terminal_execution"
                and any(
                    keyword.arg == "target_status"
                    and isinstance(keyword.value, ast.Attribute)
                    and keyword.value.attr == "CANCELLED"
                    for keyword in node.keywords
                )
            ):
                cancel_methods.append(method.name)

    assert cancel_methods == ["cancel_task"]
