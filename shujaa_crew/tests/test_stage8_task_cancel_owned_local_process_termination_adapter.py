from __future__ import annotations

import ast
from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError, fields
import importlib
import inspect
from pathlib import Path
import re
import signal
from threading import Barrier, Event, Lock

import pytest

import core.manager.service as service_module
from core.manager.service import ShujaaManager
from core.policy.contracts import (
    ActorRef,
    AuthorizationContext,
    AuthorizationDecision,
    AuthorizationEffect,
    AuthorizationRequest,
    ResourceRef,
)
from core.runtime.process_registry import ProcessRegistry
from core.runtime.process_registry_contract import ProcessOwnership
from core.tasks.store import InMemoryTaskStore, TaskRecord
from core.work.event_store import (
    AppendReceipt,
    InMemoryAuditStore,
    InMemoryEventStore,
)
from core.work.events import AppendResult
from core.work.execution_registry import InMemoryExecutionRegistry
from core.work.models import Execution, ExecutionStatus


_APP_ROOT = Path(__file__).resolve().parents[1]
_MANAGER_PATH = _APP_ROOT / "core" / "manager" / "service.py"
_API_PATH = _APP_ROOT / "apps" / "api" / "app.py"
_ADAPTER_PATH = (
    _APP_ROOT
    / "adapters"
    / "runtime"
    / "local_process_termination.py"
)
_CONTRACT_MODULE = (
    "core.runtime.owned_local_process_termination_contract"
)
_ADAPTER_MODULE = "adapters.runtime.local_process_termination"

_ACTOR = ActorRef(
    actor_type="service",
    actor_id="stage8-red-local-api",
)

_EXPECTED_DISPOSITIONS = {
    "graceful_termination",
    "forced_termination",
    "already_exited",
    "identity_mismatch",
    "process_group_mismatch",
    "ownership_verification_failure",
    "unsupported_operation",
    "termination_failure",
    "outcome_unknown",
}

_FORBIDDEN_CONTRACT_FIELDS = {
    "actor",
    "principal",
    "policy_version",
    "authorization_decision",
    "authorization_evidence",
    "authorization_evidence_reference",
    "api_key",
    "headers",
    "command",
    "payload",
    "raw_exception",
}


class _UnusedRunner:
    def start(self, topic):
        raise AssertionError("Runner must not start during cancel RED.")


class _AllowEvaluator:
    def __init__(self, trace=None):
        self.trace = trace

    def evaluate(self, request):
        if self.trace is not None:
            self.trace.append("authorization")
        return AuthorizationDecision(
            effect=AuthorizationEffect.ALLOW,
            reason_code="cancel_allowed",
            policy_version="stage8-red-policy-v1",
        )


class _DenyEvaluator:
    def evaluate(self, request):
        return AuthorizationDecision(
            effect=AuthorizationEffect.DENY,
            reason_code="cancel_denied",
            policy_version="stage8-red-policy-v1",
        )


class _TracingRegistry:
    def __init__(self, delegate, trace=None):
        self.delegate = delegate
        self.trace = trace

    def register(self, ownership):
        return self.delegate.register(ownership)

    def get(self, task_id):
        if self.trace is not None:
            self.trace.append("ownership_get")
        return self.delegate.get(task_id)

    def release(self, task_id, *, expected_execution_id):
        if self.trace is not None:
            self.trace.append("ownership_release")
        return self.delegate.release(
            task_id,
            expected_execution_id=expected_execution_id,
        )

    def claim_termination(
        self,
        ownership,
        *,
        cleanup_operation_id,
    ):
        if self.trace is not None:
            self.trace.append("ownership_claim")
        return self.delegate.claim_termination(
            ownership,
            cleanup_operation_id=cleanup_operation_id,
        )

    def finalize_termination_claim(
        self,
        ownership,
        *,
        cleanup_operation_id,
        decision,
    ):
        if self.trace is not None:
            self.trace.append("ownership_finalize")
        return self.delegate.finalize_termination_claim(
            ownership,
            cleanup_operation_id=cleanup_operation_id,
            decision=decision,
        )

    def all(self):
        return self.delegate.all()


class _TracingAuditStore:
    def __init__(
        self,
        *,
        trace=None,
        fail_authorization=False,
        raise_cleanup=False,
    ):
        self.delegate = InMemoryAuditStore()
        self.trace = trace
        self.fail_authorization = fail_authorization
        self.raise_cleanup = raise_cleanup

    def append(self, record):
        return self.append_replay_stable(record)

    def append_replay_stable(self, record):
        if self.trace is not None:
            self.trace.append(f"audit:{record.action}")
        if (
            self.fail_authorization
            and record.action == "authorization.task.cancel"
        ):
            return AppendReceipt(
                result=AppendResult.WRITE_FAILED,
                record_id=None,
                error_code="authorization_audit_unavailable",
            )
        if (
            self.raise_cleanup
            and record.action == "process_ownership.cleanup"
        ):
            raise RuntimeError(
                "secret cleanup audit backend detail"
            )
        return self.delegate.append_replay_stable(record)

    def verify_integrity(self):
        return self.delegate.verify_integrity()

    def get(self, record_id):
        return self.delegate.get(record_id)

    def list(self, after_sequence=0, limit=None):
        return self.delegate.list(after_sequence, limit)


class _TracingEventStore:
    def __init__(self, trace=None):
        self.delegate = InMemoryEventStore()
        self.trace = trace

    def append(self, record):
        if self.trace is not None:
            self.trace.append(f"event:{record.event_type}")
        return self.delegate.append(record)

    def append_replay_stable(self, record):
        if self.trace is not None:
            self.trace.append(f"event:{record.event_type}")
        return self.delegate.append_replay_stable(record)

    def verify_integrity(self):
        return self.delegate.verify_integrity()

    def get(self, record_id):
        return self.delegate.get(record_id)

    def list(self, after_sequence=0, limit=None):
        return self.delegate.list(after_sequence, limit)


class _ResultAdapter:
    def __init__(self, outcome, *, trace=None):
        self.outcome = outcome
        self.trace = trace
        self.commands = []

    def terminate(self, command):
        self.commands.append(command)
        if self.trace is not None:
            self.trace.append("adapter")
        if isinstance(self.outcome, BaseException):
            raise self.outcome
        return self.outcome


class _BlockingAdapter:
    def __init__(self, outcome):
        self.outcome = outcome
        self.entered = Event()
        self.release = Event()
        self._commands_lock = Lock()
        self.commands = []

    def terminate(self, command):
        with self._commands_lock:
            self.commands.append(command)
        self.entered.set()
        if not self.release.wait(timeout=3):
            raise AssertionError(
                "Blocked RED adapter was not released deterministically."
            )
        return self.outcome


def _load_module(module_name: str):
    try:
        return importlib.import_module(module_name)
    except ModuleNotFoundError as error:
        if error.name == module_name:
            pytest.fail(
                f"Required Slice 8.1 module is absent: {module_name}"
            )
        raise


def _contract_types():
    module = _load_module(_CONTRACT_MODULE)
    return (
        module,
        module.OwnedLocalProcessTerminationCommand,
        module.OwnedLocalProcessTerminationDisposition,
        module.OwnedLocalProcessTerminationResult,
    )


def _claim_contract_types():
    module = importlib.import_module(
        "core.runtime.process_registry_contract"
    )
    expected = (
        "TerminationClaimDisposition",
        "TerminationClaimResult",
        "TerminationFinalizeDecision",
    )
    missing = [name for name in expected if not hasattr(module, name)]
    assert missing == [], (
        "Slice 8.1 atomic ownership claim contract is absent: "
        f"{missing}"
    )
    return tuple(getattr(module, name) for name in expected)


def _claim(registry, ownership, operation_id):
    claim = getattr(registry, "claim_termination", None)
    assert callable(claim), (
        "ProcessRegistry.claim_termination is required by the "
        "bounded local atomic ownership claim contract."
    )
    return claim(
        ownership,
        cleanup_operation_id=operation_id,
    )


def _finalize(
    registry,
    ownership,
    operation_id,
    decision_name,
):
    _, _, decision_type = _claim_contract_types()
    finalize = getattr(
        registry,
        "finalize_termination_claim",
        None,
    )
    assert callable(finalize), (
        "ProcessRegistry.finalize_termination_claim is required by "
        "the bounded local atomic ownership claim contract."
    )
    return finalize(
        ownership,
        cleanup_operation_id=operation_id,
        decision=decision_type[decision_name],
    )


def _disposition_name(result):
    return result.disposition.name


def _ownership(*, task_id="task-stage8", execution_id="exec-stage8"):
    return ProcessOwnership(
        task_id=task_id,
        execution_id=execution_id,
        pid=4101,
        pgid=4201,
        process_start_time_ticks=4301,
    )


def _result(disposition_value: str):
    _, _, disposition_type, result_type = _contract_types()
    return result_type(
        disposition=disposition_type(disposition_value)
    )


def _request(task_id: str, operation_id: str):
    return AuthorizationRequest(
        actor=_ACTOR,
        action="task.cancel",
        resource=ResourceRef(
            resource_type="task",
            resource_id=task_id,
        ),
        context=AuthorizationContext(
            request_id=f"request-{operation_id}",
            operation_id=operation_id,
        ),
    )


def _cancel(
    manager,
    task_id,
    *,
    suffix,
):
    cancel_operation_id = f"op-stage8-cancel-{suffix}"
    return manager.cancel_task(
        task_id,
        authorization_request=_request(
            task_id,
            cancel_operation_id,
        ),
        cancel_operation_id=cancel_operation_id,
        cleanup_operation_id=f"op-stage8-cleanup-{suffix}",
    )


def _seed(manager, registry, *, suffix):
    task_id = f"task-stage8-{suffix}"
    execution_id = f"exec-stage8-{suffix}"
    work_id = f"work-stage8-{suffix}"
    manager.task_store.create(
        TaskRecord(
            task_id=task_id,
            work_id=work_id,
            command="sensitive command must remain outside runtime contract",
            status="running",
            process_id=4101,
            process_group_id=4201,
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
        task_id=task_id,
        execution_id=execution_id,
    )
    registry.register(owner)
    return task_id, execution_id, owner


def _manager(
    registry,
    *,
    adapter,
    trace=None,
    audit_store=None,
    event_store=None,
):
    return ShujaaManager(
        crew_runner=_UnusedRunner(),
        process_registry=registry,
        cancel_authorization_evaluator=_AllowEvaluator(trace),
        audit_store=(audit_store or _TracingAuditStore(trace=trace)),
        event_store=(event_store or _TracingEventStore(trace=trace)),
        owned_local_process_termination_adapter=adapter,
    )


def _manager_for_claim_red(
    registry,
    *,
    adapter,
    evaluator=None,
):
    manager = ShujaaManager(
        crew_runner=_UnusedRunner(),
        process_registry=registry,
        cancel_authorization_evaluator=(
            evaluator or _AllowEvaluator()
        ),
    )
    manager.owned_local_process_termination_adapter = adapter
    return manager


def _function_source(owner, name):
    return inspect.getsource(getattr(owner, name))


def test_technical_contracts_are_immutable_and_minimal():
    _, command_type, disposition_type, result_type = _contract_types()
    owner = _ownership()
    command = command_type(ownership=owner)
    result = result_type(
        disposition=disposition_type.GRACEFUL_TERMINATION
    )

    assert {item.name for item in fields(command_type)} == {
        "ownership"
    }
    assert {item.name for item in fields(result_type)} == {
        "disposition"
    }
    for contract in (command, result):
        with pytest.raises(FrozenInstanceError):
            setattr(contract, fields(contract)[0].name, object())
        assert (
            {item.name for item in fields(contract)}
            & _FORBIDDEN_CONTRACT_FIELDS
        ) == set()


def test_operation_id_is_not_a_runtime_permit_or_authority_payload():
    _, command_type, _, result_type = _contract_types()
    exposed_fields = {
        item.name
        for contract_type in (command_type, result_type)
        for item in fields(contract_type)
    }
    assert "operation_id" not in exposed_fields
    assert exposed_fields.isdisjoint(_FORBIDDEN_CONTRACT_FIELDS)


def test_result_dispositions_are_bounded_technical_outcomes():
    _, _, disposition_type, _ = _contract_types()
    assert {item.value for item in disposition_type} == (
        _EXPECTED_DISPOSITIONS
    )


def test_adapter_boundary_is_technical_only():
    contract_module, _, _, _ = _contract_types()
    adapter_module = _load_module(_ADAPTER_MODULE)

    assert hasattr(
        contract_module,
        "OwnedLocalProcessTerminationAdapterProtocol",
    )
    assert hasattr(adapter_module, "LocalProcessTerminationAdapter")
    assert hasattr(
        adapter_module.LocalProcessTerminationAdapter,
        "terminate",
    )

    tree = ast.parse(_ADAPTER_PATH.read_text(encoding="utf-8"))
    imported_roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(
                alias.name for alias in node.names
            )
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module)

    forbidden_import_prefixes = (
        "apps.api",
        "core.manager",
        "core.policy",
    )
    assert not any(
        imported.startswith(forbidden_import_prefixes)
        for imported in imported_roots
    )


@pytest.mark.parametrize(
    (
        "start_time",
        "current_pgid",
        "expected_disposition",
        "expected_signals",
    ),
    (
        (None, 4201, "already_exited", ()),
        (9999, 4201, "identity_mismatch", ()),
        (4301, 9999, "process_group_mismatch", ()),
    ),
)
def test_adapter_verifies_identity_before_signals(
    monkeypatch,
    start_time,
    current_pgid,
    expected_disposition,
    expected_signals,
):
    module, command_type, _, _ = _contract_types()
    adapter_module = _load_module(_ADAPTER_MODULE)
    adapter = adapter_module.LocalProcessTerminationAdapter(
        grace_period_seconds=0
    )
    monkeypatch.setattr(
        adapter,
        "_read_process_start_time_ticks",
        lambda pid: start_time,
    )
    monkeypatch.setattr(
        adapter_module.os,
        "getpgid",
        lambda pid: current_pgid,
    )
    sent_signals = []
    monkeypatch.setattr(
        adapter_module.os,
        "killpg",
        lambda pgid, sent_signal: sent_signals.append(sent_signal),
    )

    result = adapter.terminate(
        command_type(ownership=_ownership())
    )

    assert result.disposition.value == expected_disposition
    assert tuple(sent_signals) == expected_signals
    assert module is not None


def test_adapter_graceful_and_forced_termination_are_classified(
    monkeypatch,
):
    _, command_type, _, _ = _contract_types()
    adapter_module = _load_module(_ADAPTER_MODULE)
    owner = _ownership()

    def build_adapter():
        adapter = adapter_module.LocalProcessTerminationAdapter(
            grace_period_seconds=0
        )
        monkeypatch.setattr(
            adapter,
            "_read_process_start_time_ticks",
            lambda pid: owner.process_start_time_ticks,
        )
        monkeypatch.setattr(
            adapter_module.os,
            "getpgid",
            lambda pid: owner.pgid,
        )
        return adapter

    graceful_calls = []

    def graceful_exit(pgid, sent_signal):
        graceful_calls.append(sent_signal)
        if sent_signal == 0:
            raise ProcessLookupError

    monkeypatch.setattr(adapter_module.os, "killpg", graceful_exit)
    graceful = build_adapter().terminate(
        command_type(ownership=owner)
    )
    assert graceful.disposition.value == "graceful_termination"
    assert graceful_calls == [signal.SIGTERM, 0]

    forced_calls = []

    def forced_exit(pgid, sent_signal):
        forced_calls.append(sent_signal)
        if sent_signal == 0 and signal.SIGKILL in forced_calls:
            raise ProcessLookupError

    monkeypatch.setattr(adapter_module.os, "killpg", forced_exit)
    forced = build_adapter().terminate(
        command_type(ownership=owner)
    )
    assert forced.disposition.value == "forced_termination"
    assert forced_calls == [signal.SIGTERM, 0, signal.SIGKILL, 0]


@pytest.mark.parametrize(
    ("failure", "expected_disposition"),
    (
        (PermissionError("identity unavailable"), "ownership_verification_failure"),
        (RuntimeError("termination failed"), "termination_failure"),
    ),
)
def test_adapter_failures_return_structured_results_without_raw_error(
    monkeypatch,
    failure,
    expected_disposition,
):
    _, command_type, _, _ = _contract_types()
    adapter_module = _load_module(_ADAPTER_MODULE)
    adapter = adapter_module.LocalProcessTerminationAdapter(
        grace_period_seconds=0
    )
    owner = _ownership()
    if expected_disposition == "ownership_verification_failure":
        def fail_identity(pid):
            raise failure

        monkeypatch.setattr(
            adapter,
            "_read_process_start_time_ticks",
            fail_identity,
        )
    else:
        monkeypatch.setattr(
            adapter,
            "_read_process_start_time_ticks",
            lambda pid: owner.process_start_time_ticks,
        )
        monkeypatch.setattr(
            adapter_module.os,
            "getpgid",
            lambda pid: owner.pgid,
        )

        def fail_signal(pgid, sent_signal):
            raise failure

        monkeypatch.setattr(
            adapter_module.os,
            "killpg",
            fail_signal,
        )

    result = adapter.terminate(command_type(ownership=owner))
    assert result.disposition.value == expected_disposition
    assert str(failure) not in repr(result)


def test_manager_orders_authority_lifecycle_ownership_adapter_and_audit(
    tmp_path,
):
    trace = []
    delegate = ProcessRegistry(tmp_path / "processes.json")
    registry = _TracingRegistry(delegate, trace)
    adapter = _ResultAdapter(
        _result("graceful_termination"),
        trace=trace,
    )
    manager = _manager(registry, adapter=adapter, trace=trace)
    task_id, _, _ = _seed(manager, registry, suffix="ordering")
    trace.clear()
    original_reconcile = manager._reconcile_terminal_execution

    def reconcile(*args, **kwargs):
        result = original_reconcile(*args, **kwargs)
        trace.append("lifecycle")
        return result

    manager._reconcile_terminal_execution = reconcile

    response = _cancel(manager, task_id, suffix="ordering")

    expected_order = (
        "authorization",
        "audit:authorization.task.cancel",
        "lifecycle",
        "ownership_get",
        "adapter",
        "ownership_release",
    )
    positions = [trace.index(item) for item in expected_order]
    assert positions == sorted(positions)
    cleanup_event_position = next(
        index
        for index, item in enumerate(trace)
        if item.startswith("event:process_ownership.cleanup.")
    )
    cleanup_audit_position = trace.index(
        "audit:process_ownership.cleanup"
    )
    assert positions[-1] < cleanup_event_position < cleanup_audit_position
    assert response["status"] == "cancelled"


@pytest.mark.parametrize(
    ("disposition", "ownership_released"),
    (
        ("graceful_termination", True),
        ("forced_termination", True),
        ("already_exited", True),
        ("identity_mismatch", False),
        ("process_group_mismatch", False),
        ("ownership_verification_failure", False),
        ("unsupported_operation", False),
        ("termination_failure", False),
        ("outcome_unknown", False),
    ),
)
def test_manager_releases_ownership_only_for_proven_safe_outcomes(
    tmp_path,
    disposition,
    ownership_released,
):
    registry = ProcessRegistry(tmp_path / f"{disposition}.json")
    adapter = _ResultAdapter(_result(disposition))
    manager = _manager(registry, adapter=adapter)
    task_id, execution_id, owner = _seed(
        manager,
        registry,
        suffix=disposition,
    )

    response = _cancel(manager, task_id, suffix=disposition)

    assert len(adapter.commands) == 1
    assert (registry.get(task_id) is None) is ownership_released
    if not ownership_released:
        assert registry.get(task_id) == owner
    assert response["status"] == "cancelled"
    assert manager.execution_registry.get(execution_id).status is (
        ExecutionStatus.CANCELLED
    )


@pytest.mark.parametrize("mode", ("missing", "exception", "malformed"))
def test_missing_or_broken_adapter_fails_safe_without_direct_fallback(
    tmp_path,
    mode,
):
    registry = ProcessRegistry(tmp_path / f"{mode}.json")
    kwargs = {
        "crew_runner": _UnusedRunner(),
        "process_registry": registry,
        "cancel_authorization_evaluator": _AllowEvaluator(),
    }
    if mode == "exception":
        kwargs["owned_local_process_termination_adapter"] = (
            _ResultAdapter(RuntimeError("secret adapter failure"))
        )
    elif mode == "malformed":
        kwargs["owned_local_process_termination_adapter"] = (
            _ResultAdapter(object())
        )
    manager = ShujaaManager(**kwargs)
    task_id, execution_id, owner = _seed(
        manager,
        registry,
        suffix=f"broken-{mode}",
    )
    direct_calls = []

    def forbidden_direct_fallback(pgid):
        direct_calls.append(pgid)
        raise AssertionError("direct POSIX fallback is forbidden")

    manager._terminate_process_group_by_id = forbidden_direct_fallback

    response = _cancel(manager, task_id, suffix=f"broken-{mode}")

    assert direct_calls == []
    assert registry.get(task_id) == owner
    assert response["status"] == "cancelled"
    assert response["cleanup_error"] is None
    assert "secret adapter failure" not in repr(response)
    assert manager.execution_registry.get(execution_id).status is (
        ExecutionStatus.CANCELLED
    )


@pytest.mark.parametrize(
    "disposition",
    ("graceful_termination", "outcome_unknown"),
)
def test_replay_never_retries_a_proven_success_or_unknown_outcome(
    tmp_path,
    disposition,
):
    registry = ProcessRegistry(tmp_path / f"replay-{disposition}.json")
    adapter = _ResultAdapter(_result(disposition))
    manager = _manager(registry, adapter=adapter)
    task_id, _, _ = _seed(
        manager,
        registry,
        suffix=f"replay-{disposition}",
    )

    first = _cancel(manager, task_id, suffix=f"{disposition}-first")
    second = _cancel(manager, task_id, suffix=f"{disposition}-second")

    assert first["status"] == second["status"] == "cancelled"
    assert len(adapter.commands) == 1


def test_pre_action_evidence_failure_blocks_adapter_and_lifecycle(
    tmp_path,
):
    registry = ProcessRegistry(tmp_path / "pre-action.json")
    adapter = _ResultAdapter(_result("graceful_termination"))
    audit_store = _TracingAuditStore(fail_authorization=True)
    manager = _manager(
        registry,
        adapter=adapter,
        audit_store=audit_store,
    )
    task_id, execution_id, owner = _seed(
        manager,
        registry,
        suffix="pre-action",
    )

    with pytest.raises(Exception) as captured:
        _cancel(manager, task_id, suffix="pre-action")

    assert getattr(captured.value, "reason_code", None) == (
        "AUDIT_UNAVAILABLE"
    )
    assert adapter.commands == []
    assert registry.get(task_id) == owner
    assert manager.execution_registry.get(execution_id).status is (
        ExecutionStatus.RUNNING
    )


def test_cleanup_audit_exception_preserves_termination_and_is_sanitized(
    tmp_path,
    caplog,
):
    registry = ProcessRegistry(tmp_path / "audit-failure.json")
    adapter = _ResultAdapter(_result("graceful_termination"))
    audit_store = _TracingAuditStore(raise_cleanup=True)
    manager = _manager(
        registry,
        adapter=adapter,
        audit_store=audit_store,
    )
    task_id, execution_id, _ = _seed(
        manager,
        registry,
        suffix="audit-failure",
    )

    with caplog.at_level("WARNING", logger="core.manager.service"):
        response = _cancel(manager, task_id, suffix="audit-failure")

    assert response["status"] == "cancelled"
    assert len(adapter.commands) == 1
    assert registry.get(task_id) is None
    assert manager.execution_registry.get(execution_id).status is (
        ExecutionStatus.CANCELLED
    )
    diagnostics = [
        record
        for record in caplog.records
        if getattr(record, "diagnostic_code", None)
        == "POST_ACTION_AUDIT_FAILED"
    ]
    assert len(diagnostics) == 1
    diagnostic = diagnostics[0]

    # RED_CONTRACT_TEST_CORRECTION=SANITIZATION_CHECK_SCOPED_TO_SHUJAA_CONTROLLED_LOG_OUTPUTS_WITH_NUMERIC_TOKEN_BOUNDARIES
    def contains_numeric_identifier(value, identifier):
        if type(value) is int:
            return value == identifier
        if isinstance(value, str):
            return re.search(
                rf"(?<!\d){identifier}(?!\d)",
                value,
            ) is not None
        if isinstance(value, dict):
            return any(
                contains_numeric_identifier(item, identifier)
                for pair in value.items()
                for item in pair
            )
        if isinstance(value, (list, tuple, set, frozenset)):
            return any(
                contains_numeric_identifier(item, identifier)
                for item in value
            )
        return False

    def contains_text(value, forbidden):
        if isinstance(value, str):
            return forbidden in value
        if isinstance(value, dict):
            return any(
                contains_text(item, forbidden)
                for pair in value.items()
                for item in pair
            )
        if isinstance(value, (list, tuple, set, frozenset)):
            return any(
                contains_text(item, forbidden)
                for item in value
            )
        return False

    shujaa_controlled_outputs = {
        "message": diagnostic.getMessage(),
        "formatted_args": tuple(
            str(argument) for argument in diagnostic.args
        ),
        "extra": {
            field: getattr(diagnostic, field)
            for field in (
                "diagnostic_code",
                "exception_type",
                "operation_id",
                "resource_type",
                "resource_id",
            )
        },
        "structured_cleanup_outcome": {
            "status": response["status"],
            "cleanup_disposition": response["cleanup_disposition"],
            "cleanup_error": response["cleanup_error"],
            "cleanup_audit_append_receipt": response[
                "cleanup_audit_append_receipt"
            ],
            "adapter_disposition": adapter.outcome.disposition.value,
        },
    }

    assert contains_numeric_identifier("4101", 4101)
    assert contains_numeric_identifier("pid=4101", 4101)
    assert contains_numeric_identifier(4101, 4101)
    assert not contains_numeric_identifier(
        "thread=123741015983936",
        4101,
    )

    for forbidden in (
        "secret cleanup audit backend detail",
        "Traceback",
    ):
        assert not contains_text(shujaa_controlled_outputs, forbidden)
    for sensitive_identifier in (4101, 4201, 4301):
        assert not contains_numeric_identifier(
            shujaa_controlled_outputs,
            sensitive_identifier,
        )


def test_cancel_path_uses_adapter_without_manager_posix_bypass():
    cancel_source = _function_source(ShujaaManager, "cancel_task")
    assert "owned_local_process_termination_adapter" in cancel_source
    assert "_cleanup_process_ownership(" not in cancel_source
    assert "_terminate_process_group_by_id" not in cancel_source
    assert "os.kill" not in cancel_source
    assert "killpg" not in cancel_source


def test_api_does_not_call_adapter_or_publish_termination_command():
    api_source = _API_PATH.read_text(encoding="utf-8")
    manager_source = _MANAGER_PATH.read_text(encoding="utf-8")
    api_tree = ast.parse(api_source)
    cancel_function = next(
        node
        for node in api_tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "cancel_task"
    )
    cancel_call_attributes = {
        node.func.attr
        for node in ast.walk(cancel_function)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
    }
    assert cancel_call_attributes.isdisjoint(
        {
            "terminate",
            "kill",
            "killpg",
            "_terminate_process_group_by_id",
        }
    )

    adapter_imports = [
        node
        for node in api_tree.body
        if isinstance(node, ast.ImportFrom)
        and node.module
        == "adapters.runtime.local_process_termination"
    ]
    assert len(adapter_imports) == 1
    assert [alias.name for alias in adapter_imports[0].names] == [
        "LocalProcessTerminationAdapter"
    ]
    adapter_constructors = [
        node
        for node in ast.walk(api_tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "LocalProcessTerminationAdapter"
    ]
    assert len(adapter_constructors) == 1
    manager_constructors = [
        node
        for node in ast.walk(api_tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "ShujaaManager"
    ]
    assert len(manager_constructors) == 1
    adapter_keywords = [
        keyword
        for keyword in manager_constructors[0].keywords
        if keyword.arg == "owned_local_process_termination_adapter"
    ]
    assert len(adapter_keywords) == 1

    manager_tree = ast.parse(manager_source)
    manager_class = next(
        node
        for node in manager_tree.body
        if isinstance(node, ast.ClassDef)
        and node.name == "ShujaaManager"
    )
    manager_cancel = next(
        node
        for node in manager_class.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "cancel_task"
    )
    manager_cancel_call_attributes = {
        node.func.attr
        for node in ast.walk(manager_cancel)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
    }
    assert "_terminate_process_group_by_id" not in (
        manager_cancel_call_attributes
    )
    assert manager_cancel_call_attributes.isdisjoint({"kill", "killpg"})
    assert "execution.terminate" not in api_source
    assert "execution.terminate" not in manager_source


def test_api_cancel_uses_composition_root_injected_adapter(
    tmp_path,
    monkeypatch,
):
    api_module = importlib.import_module("apps.api.app")
    configured_manager = api_module.manager
    configured_adapter = (
        configured_manager.owned_local_process_termination_adapter
    )

    assert isinstance(
        configured_adapter,
        api_module.LocalProcessTerminationAdapter,
    )
    assert configured_adapter is (
        api_module.owned_local_process_termination_adapter
    )

    registry = ProcessRegistry(tmp_path / "api-composition.json")
    monkeypatch.setattr(
        configured_manager,
        "task_store",
        InMemoryTaskStore(),
    )
    monkeypatch.setattr(
        configured_manager,
        "execution_registry",
        InMemoryExecutionRegistry(),
    )
    monkeypatch.setattr(
        configured_manager,
        "process_registry",
        registry,
    )
    monkeypatch.setattr(
        configured_manager,
        "event_store",
        InMemoryEventStore(),
    )
    monkeypatch.setattr(
        configured_manager,
        "audit_store",
        InMemoryAuditStore(),
    )

    adapter_commands = []

    def terminate_without_posix(command):
        adapter_commands.append(command)
        return _result("graceful_termination")

    monkeypatch.setattr(
        configured_adapter,
        "terminate",
        terminate_without_posix,
    )
    legacy_calls = []
    monkeypatch.setattr(
        configured_manager,
        "_terminate_process_group_by_id",
        legacy_calls.append,
    )

    task_id, _, owner = _seed(
        configured_manager,
        registry,
        suffix="api-composition",
    )
    api_key = "stage8-api-composition-test-key"
    monkeypatch.setenv("SHUJAA_API_KEY", api_key)

    response = api_module.app.test_client().post(
        f"/tasks/{task_id}/cancel",
        headers={"X-Shujaa-Key": api_key},
    )

    assert response.status_code == 200
    assert response.get_json()["status"] == "cancelled"
    assert [command.ownership for command in adapter_commands] == [owner]
    assert legacy_calls == []
    assert registry.get(task_id) is None


def test_non_migrated_cleanup_paths_do_not_claim_slice_8_1_adapter():
    bulk_cleanup_source = _function_source(
        ShujaaManager,
        "cleanup_registered_processes",
    )
    assert "owned_local_process_termination_adapter" not in (
        bulk_cleanup_source
    )
    assert not (_APP_ROOT / "core" / "runtime" / "timeout_adapter.py").exists()
    assert not (_APP_ROOT / "core" / "runtime" / "shutdown_adapter.py").exists()
    assert not (_APP_ROOT / "core" / "runtime" / "startup_adapter.py").exists()


def test_concurrent_cancel_characterizes_duplicate_side_effect_gap(
    tmp_path,
):
    registry = ProcessRegistry(tmp_path / "concurrency.json")
    adapter = _BlockingAdapter(_result("graceful_termination"))
    side_effect_attempts = adapter.commands
    manager = _manager_for_claim_red(registry, adapter=adapter)
    task_id, _, _ = _seed(
        manager,
        registry,
        suffix="concurrency",
    )
    fallback_calls = []
    manager._terminate_process_group_by_id = fallback_calls.append
    start = Barrier(3)

    def invoke(suffix):
        start.wait(timeout=3)
        return _cancel(manager, task_id, suffix=suffix)

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(invoke, "concurrent-a"),
            executor.submit(invoke, "concurrent-b"),
        ]
        start.wait(timeout=3)
        adapter_entered = adapter.entered.wait(timeout=3)
        adapter.release.set()
        responses = [future.result(timeout=5) for future in futures]

    assert adapter_entered
    assert len(side_effect_attempts) == 1, (
        "The same verified local ownership crossed the termination "
        "adapter boundary more than once under two concurrent cancel "
        "attempts."
    )
    assert fallback_calls == []
    assert [response["status"] for response in responses] == [
        "cancelled",
        "cancelled",
    ]
    assert registry.get(task_id) is None


def test_concurrency_requirement_is_bounded_to_shared_ownership():
    source = inspect.getsource(
        test_concurrent_cancel_characterizes_duplicate_side_effect_gap
    )
    assert "same verified local ownership" in source
    assert "len(side_effect_attempts) == 1" in source


def test_claim_contract_exposes_only_bounded_local_technical_states():
    disposition_type, result_type, decision_type = (
        _claim_contract_types()
    )
    assert {
        "ACQUIRED",
        "NOT_FOUND",
        "OWNERSHIP_MISMATCH",
        "CLAIMED_BY_OTHER_OPERATION",
        "SAME_OPERATION_REPLAY",
        "FINALIZED_AND_RELEASED",
        "OUTCOME_UNKNOWN_BLOCKED",
    } <= set(disposition_type.__members__)
    assert set(decision_type.__members__) == {
        "RELEASE_OWNERSHIP",
        "RETAIN_OWNERSHIP_AND_RELEASE_CLAIM",
        "RETAIN_OWNERSHIP_AND_QUARANTINE",
    }
    assert {
        item.name for item in fields(result_type)
    }.isdisjoint(_FORBIDDEN_CONTRACT_FIELDS)

    contract_module = importlib.import_module(
        "core.runtime.process_registry_contract"
    )
    protocol = contract_module.ProcessRegistryProtocol
    assert hasattr(protocol, "claim_termination")
    assert hasattr(protocol, "finalize_termination_claim")


def test_registry_claim_rejects_not_found_and_ownership_mismatch(
    tmp_path,
):
    registry = ProcessRegistry(tmp_path / "claim-identity.json")
    owner = _ownership(task_id="claim-identity")
    not_found = _claim(registry, owner, "cleanup-not-found")
    assert _disposition_name(not_found) == "NOT_FOUND"

    registry.register(owner)
    different_generation = ProcessOwnership(
        task_id=owner.task_id,
        execution_id="different-execution",
        pid=owner.pid + 1,
        pgid=owner.pgid + 1,
        process_start_time_ticks=(
            owner.process_start_time_ticks + 1
        ),
    )
    mismatch = _claim(
        registry,
        different_generation,
        "cleanup-mismatch",
    )
    assert _disposition_name(mismatch) == "OWNERSHIP_MISMATCH"


def test_registry_atomic_claim_admits_one_concurrent_winner(
    tmp_path,
):
    registry = ProcessRegistry(tmp_path / "atomic-claim.json")
    owner = _ownership(task_id="atomic-claim")
    registry.register(owner)
    start = Barrier(3)

    def attempt(operation_id):
        start.wait(timeout=3)
        return _claim(registry, owner, operation_id)

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(attempt, "cleanup-winner-a"),
            executor.submit(attempt, "cleanup-winner-b"),
        ]
        start.wait(timeout=3)
        results = [future.result(timeout=3) for future in futures]

    assert sorted(_disposition_name(result) for result in results) == [
        "ACQUIRED",
        "CLAIMED_BY_OTHER_OPERATION",
    ]


def test_registry_distinguishes_same_operation_replay_and_contention(
    tmp_path,
):
    registry = ProcessRegistry(tmp_path / "operation-identity.json")
    owner = _ownership(task_id="operation-identity")
    registry.register(owner)

    acquired = _claim(registry, owner, "cleanup-owner")
    replay = _claim(registry, owner, "cleanup-owner")
    contender = _claim(registry, owner, "cleanup-contender")

    assert _disposition_name(acquired) == "ACQUIRED"
    assert _disposition_name(replay) == "SAME_OPERATION_REPLAY"
    assert _disposition_name(contender) == (
        "CLAIMED_BY_OTHER_OPERATION"
    )


def test_different_exact_ownership_keys_do_not_block_each_other(
    tmp_path,
):
    registry = ProcessRegistry(tmp_path / "different-keys.json")
    owners = (
        _ownership(task_id="different-key-a", execution_id="exec-a"),
        _ownership(task_id="different-key-b", execution_id="exec-b"),
    )
    for owner in owners:
        registry.register(owner)
    start = Barrier(3)

    def claim_owner(owner, operation_id):
        start.wait(timeout=3)
        return _claim(registry, owner, operation_id)

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(
                claim_owner,
                owners[0],
                "cleanup-key-a",
            ),
            executor.submit(
                claim_owner,
                owners[1],
                "cleanup-key-b",
            ),
        ]
        start.wait(timeout=3)
        results = [future.result(timeout=3) for future in futures]

    assert [_disposition_name(result) for result in results] == [
        "ACQUIRED",
        "ACQUIRED",
    ]


def test_replaced_ownership_generation_is_not_blocked_by_old_claim(
    tmp_path,
):
    registry = ProcessRegistry(tmp_path / "new-generation.json")
    first = _ownership(
        task_id="same-task-new-generation",
        execution_id="generation-one",
    )
    registry.register(first)
    assert _disposition_name(
        _claim(registry, first, "cleanup-generation-one")
    ) == "ACQUIRED"
    finalized = _finalize(
        registry,
        first,
        "cleanup-generation-one",
        "RELEASE_OWNERSHIP",
    )
    assert _disposition_name(finalized) == "FINALIZED_AND_RELEASED"

    second = ProcessOwnership(
        task_id=first.task_id,
        execution_id="generation-two",
        pid=5101,
        pgid=5201,
        process_start_time_ticks=5301,
    )
    registry.register(second)
    assert _disposition_name(
        _claim(registry, second, "cleanup-generation-two")
    ) == "ACQUIRED"


def test_registry_instances_for_same_path_share_active_claim_state(
    tmp_path,
):
    path = tmp_path / "shared-path.json"
    first_registry = ProcessRegistry(path)
    second_registry = ProcessRegistry(path)
    owner = _ownership(task_id="shared-path")
    first_registry.register(owner)

    first = _claim(first_registry, owner, "cleanup-shared-a")
    second = _claim(second_registry, owner, "cleanup-shared-b")

    assert _disposition_name(first) == "ACQUIRED"
    assert _disposition_name(second) == "CLAIMED_BY_OTHER_OPERATION"


def test_claim_state_is_non_durable_and_not_written_to_registry_file(
    tmp_path,
):
    path = tmp_path / "non-durable-claim.json"
    registry = ProcessRegistry(path)
    owner = _ownership(task_id="non-durable-claim")
    registry.register(owner)
    persisted_before = path.read_bytes()

    result = _claim(registry, owner, "cleanup-memory-only")

    assert _disposition_name(result) == "ACQUIRED"
    assert path.read_bytes() == persisted_before
    assert b"cleanup-memory-only" not in path.read_bytes()


def test_finalize_release_removes_ownership_atomically(tmp_path):
    registry = ProcessRegistry(tmp_path / "finalize-release.json")
    owner = _ownership(task_id="finalize-release")
    registry.register(owner)
    assert _disposition_name(
        _claim(registry, owner, "cleanup-finalize-release")
    ) == "ACQUIRED"

    result = _finalize(
        registry,
        owner,
        "cleanup-finalize-release",
        "RELEASE_OWNERSHIP",
    )

    assert _disposition_name(result) == "FINALIZED_AND_RELEASED"
    assert registry.get(owner.task_id) is None


def test_proven_pre_side_effect_failure_retains_owner_and_releases_claim(
    tmp_path,
):
    registry = ProcessRegistry(tmp_path / "pre-side-effect.json")
    owner = _ownership(task_id="pre-side-effect")
    registry.register(owner)
    assert _disposition_name(
        _claim(registry, owner, "cleanup-pre-side-effect-a")
    ) == "ACQUIRED"

    _finalize(
        registry,
        owner,
        "cleanup-pre-side-effect-a",
        "RETAIN_OWNERSHIP_AND_RELEASE_CLAIM",
    )

    assert registry.get(owner.task_id) == owner
    assert _disposition_name(
        _claim(registry, owner, "cleanup-pre-side-effect-b")
    ) == "ACQUIRED"


def test_concurrent_manager_calls_admit_one_adapter_invocation(
    tmp_path,
):
    registry = ProcessRegistry(tmp_path / "manager-concurrency.json")
    adapter = _BlockingAdapter(_result("graceful_termination"))
    manager = _manager_for_claim_red(registry, adapter=adapter)
    task_id, _, _ = _seed(
        manager,
        registry,
        suffix="manager-concurrency",
    )
    fallback_calls = []
    manager._terminate_process_group_by_id = fallback_calls.append
    start = Barrier(3)

    def invoke(suffix):
        start.wait(timeout=3)
        return _cancel(manager, task_id, suffix=suffix)

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(invoke, "claim-contender-a"),
            executor.submit(invoke, "claim-contender-b"),
        ]
        start.wait(timeout=3)
        adapter_entered = adapter.entered.wait(timeout=3)
        adapter.release.set()
        responses = [future.result(timeout=5) for future in futures]

    assert adapter_entered
    assert len(adapter.commands) == 1
    assert fallback_calls == []
    assert [response["status"] for response in responses] == [
        "cancelled",
        "cancelled",
    ]


def test_registry_path_lock_is_released_while_adapter_is_blocked(
    tmp_path,
):
    path = tmp_path / "adapter-lock-release.json"
    manager_registry = ProcessRegistry(path)
    observer_registry = ProcessRegistry(path)
    adapter = _BlockingAdapter(_result("graceful_termination"))
    manager = _manager_for_claim_red(
        manager_registry,
        adapter=adapter,
    )
    task_id, _, owner = _seed(
        manager,
        manager_registry,
        suffix="adapter-lock-release",
    )

    with ThreadPoolExecutor(max_workers=2) as executor:
        cancel_future = executor.submit(
            _cancel,
            manager,
            task_id,
            suffix="adapter-lock-release",
        )
        adapter_entered = adapter.entered.wait(timeout=3)
        try:
            assert adapter_entered
            registry_future = executor.submit(
                observer_registry.get,
                task_id,
            )
            assert registry_future.result(timeout=1) == owner
        finally:
            adapter.release.set()
        assert cancel_future.result(timeout=5)["status"] == "cancelled"


@pytest.mark.parametrize(
    "disposition",
    ("graceful_termination", "already_exited"),
)
def test_manager_finalizes_proven_safe_outcome_without_replay_signal(
    tmp_path,
    disposition,
):
    registry = ProcessRegistry(tmp_path / f"safe-{disposition}.json")
    adapter = _ResultAdapter(_result(disposition))
    manager = _manager_for_claim_red(registry, adapter=adapter)
    task_id, _, _ = _seed(
        manager,
        registry,
        suffix=f"safe-{disposition}",
    )

    first = _cancel(manager, task_id, suffix=f"safe-{disposition}-a")
    second = _cancel(manager, task_id, suffix=f"safe-{disposition}-b")

    assert first["status"] == second["status"] == "cancelled"
    assert len(adapter.commands) == 1
    assert registry.get(task_id) is None


def test_known_post_side_effect_failure_preserves_lifecycle_without_retry(
    tmp_path,
):
    registry = ProcessRegistry(tmp_path / "known-post-effect.json")
    adapter = _ResultAdapter(_result("termination_failure"))
    manager = _manager_for_claim_red(registry, adapter=adapter)
    task_id, execution_id, owner = _seed(
        manager,
        registry,
        suffix="known-post-effect",
    )

    response = _cancel(manager, task_id, suffix="known-post-effect")

    assert response["status"] == "cancelled"
    assert len(adapter.commands) == 1
    assert registry.get(task_id) == owner
    assert manager.execution_registry.get(execution_id).status is (
        ExecutionStatus.CANCELLED
    )


@pytest.mark.parametrize(
    "outcome",
    (RuntimeError("unproven adapter exception"), object()),
    ids=("exception", "malformed"),
)
def test_unproven_adapter_outcome_quarantines_claim_and_blocks_replay(
    tmp_path,
    outcome,
):
    registry = ProcessRegistry(
        tmp_path / f"unknown-{type(outcome).__name__}.json"
    )
    adapter = _ResultAdapter(outcome)
    manager = _manager_for_claim_red(registry, adapter=adapter)
    task_id, execution_id, owner = _seed(
        manager,
        registry,
        suffix=f"unknown-{type(outcome).__name__}",
    )
    fallback_calls = []
    manager._terminate_process_group_by_id = fallback_calls.append

    first = _cancel(manager, task_id, suffix="unknown-first")
    second = _cancel(manager, task_id, suffix="unknown-second")

    assert first["status"] == second["status"] == "cancelled"
    assert len(adapter.commands) == 1
    assert fallback_calls == []
    assert registry.get(task_id) == owner
    assert manager.execution_registry.get(execution_id).status is (
        ExecutionStatus.CANCELLED
    )
    blocked = _claim(registry, owner, "cleanup-after-unknown")
    assert _disposition_name(blocked) == "OUTCOME_UNKNOWN_BLOCKED"


def test_denied_authorization_never_claims_or_invokes_adapter(tmp_path):
    trace = []
    delegate = ProcessRegistry(tmp_path / "denied-no-claim.json")
    registry = _TracingRegistry(delegate, trace)
    adapter = _ResultAdapter(object())
    manager = _manager_for_claim_red(
        registry,
        adapter=adapter,
        evaluator=_DenyEvaluator(),
    )
    task_id, execution_id, owner = _seed(
        manager,
        registry,
        suffix="denied-no-claim",
    )
    trace.clear()

    with pytest.raises(Exception) as captured:
        _cancel(manager, task_id, suffix="denied-no-claim")

    assert getattr(captured.value, "reason_code", None) == "POLICY_DENIED"
    assert "ownership_claim" not in trace
    assert adapter.commands == []
    assert registry.get(task_id) == owner
    assert manager.execution_registry.get(execution_id).status is (
        ExecutionStatus.RUNNING
    )


def test_claim_contention_does_not_rewrite_lifecycle_winner(tmp_path):
    registry = ProcessRegistry(tmp_path / "contention-lifecycle.json")
    adapter = _ResultAdapter(object())
    manager = _manager_for_claim_red(registry, adapter=adapter)
    task_id, execution_id, owner = _seed(
        manager,
        registry,
        suffix="contention-lifecycle",
    )
    assert _disposition_name(
        _claim(registry, owner, "cleanup-existing-winner")
    ) == "ACQUIRED"

    response = _cancel(manager, task_id, suffix="contention-loser")

    assert response["status"] == "cancelled"
    assert adapter.commands == []
    assert registry.get(task_id) == owner
    assert manager.execution_registry.get(execution_id).status is (
        ExecutionStatus.CANCELLED
    )


def test_registry_claim_and_finalize_do_not_interpret_policy_or_signals():
    registry_path = _APP_ROOT / "core" / "runtime" / "process_registry.py"
    tree = ast.parse(registry_path.read_text(encoding="utf-8"))
    imported_modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module)

    assert not any(
        module == "signal"
        or module.startswith("core.policy")
        or module.startswith("adapters.runtime")
        for module in imported_modules
    )
