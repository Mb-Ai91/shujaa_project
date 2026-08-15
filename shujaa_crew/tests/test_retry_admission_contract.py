import pytest

from core.manager.service import ShujaaManager
from core.work.execution_registry import (
    InMemoryExecutionRegistry,
)
from core.work.models import (
    Execution,
    ExecutionStatus,
    RetrySafety,
)


def test_initial_execution_is_retry_denied_with_root_lineage():
    execution = Execution(
        execution_id="exec-initial",
        work_id="work-initial",
        task_id="task-initial",
    )

    assert execution.retry_safety == RetrySafety.DENY
    assert execution.attempt_number == 1
    assert execution.previous_execution_id is None
    assert execution.retry_operation_id is None
    assert execution.requested_agent_id is None
    assert execution.required_capability is None


def test_submit_preserves_retry_safety_and_original_routing():
    from core.work.dispatcher import DispatchDecision

    class ImmediateProcess:
        pid = 12345

        def wait(self, timeout=None):
            return 0

    class ImmediateRunner:
        def start(self, command):
            return ImmediateProcess()

    class RecordingDispatcher:
        def dispatch(self, request):
            return DispatchDecision(
                executor_id="executor-original",
                runtime_id="test-runtime",
            )

    manager = ShujaaManager(
        crew_runner=ImmediateRunner(),
        execution_dispatcher=RecordingDispatcher(),
    )

    submitted = manager.submit(
        "retryable task",
        requested_agent_id="agent-original",
        required_capability="analysis",
        retry_safety=RetrySafety.DECLARED_SAFE,
    )

    execution = manager.execution_registry.get(
        submitted["execution_id"]
    )

    assert execution is not None
    assert execution.retry_safety == RetrySafety.DECLARED_SAFE
    assert execution.requested_agent_id == "agent-original"
    assert execution.required_capability == "analysis"


def test_registry_atomically_admits_retry_with_derived_lineage():
    registry = InMemoryExecutionRegistry()
    source = Execution(
        execution_id="exec-source",
        work_id="work-1",
        task_id="task-1",
        status=ExecutionStatus.FAILED,
        retry_safety=RetrySafety.DECLARED_SAFE,
        executor_id="executor-previous",
        requested_agent_id="agent-original",
        required_capability="analysis",
    )
    registry.create(source)

    result = registry.admit_retry(
        source.execution_id,
        execution_id="exec-retry",
        operation_id="retry-operation-1",
    )

    retry = result.execution

    assert result.applied is True
    assert result.disposition.value == "applied"
    assert registry.get(retry.execution_id) == retry
    assert retry.execution_id == "exec-retry"
    assert retry.status == ExecutionStatus.QUEUED
    assert retry.attempt_number == 2
    assert retry.previous_execution_id == source.execution_id
    assert retry.retry_operation_id == "retry-operation-1"
    assert retry.retry_safety == RetrySafety.DECLARED_SAFE
    assert retry.requested_agent_id == "agent-original"
    assert retry.required_capability == "analysis"
    assert retry.executor_id is None


def test_retry_admission_is_idempotent_for_same_operation():
    registry = InMemoryExecutionRegistry()
    source = Execution(
        execution_id="exec-idempotent-source",
        work_id="work-2",
        task_id="task-2",
        status=ExecutionStatus.FAILED,
        retry_safety=RetrySafety.DECLARED_SAFE,
    )
    registry.create(source)

    first = registry.admit_retry(
        source.execution_id,
        execution_id="exec-idempotent-first",
        operation_id="retry-idempotent",
    )
    replay = registry.admit_retry(
        source.execution_id,
        execution_id="exec-idempotent-second",
        operation_id="retry-idempotent",
    )

    assert first.disposition.value == "applied"
    assert replay.applied is False
    assert replay.disposition.value == "idempotent_replay"
    assert replay.execution == first.execution
    assert (
        registry.get("exec-idempotent-second")
        is None
    )
    assert len(registry.list_by_task("task-2")) == 2


def test_concurrent_retry_operations_create_one_attempt():
    from concurrent.futures import ThreadPoolExecutor

    registry = InMemoryExecutionRegistry()
    source = Execution(
        execution_id="exec-concurrent-source",
        work_id="work-3",
        task_id="task-3",
        status=ExecutionStatus.FAILED,
        retry_safety=RetrySafety.DECLARED_SAFE,
    )
    registry.create(source)

    requests = (
        ("exec-concurrent-a", "retry-operation-a"),
        ("exec-concurrent-b", "retry-operation-b"),
    )

    def admit(request):
        execution_id, operation_id = request
        return registry.admit_retry(
            source.execution_id,
            execution_id=execution_id,
            operation_id=operation_id,
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(admit, requests))

    dispositions = {
        result.disposition.value
        for result in results
    }

    assert dispositions == {
        "applied",
        "conflicting_retry",
    }
    assert len(registry.list_by_task("task-3")) == 2
    assert len(
        {
            result.execution.execution_id
            for result in results
        }
    ) == 1


class NeverStartedRunner:
    def start(self, command):
        raise AssertionError(
            "Retry admission must not start a runner."
        )


def test_manager_denies_retry_by_default():
    manager = ShujaaManager(
        crew_runner=NeverStartedRunner()
    )
    source = Execution(
        execution_id="exec-default-deny",
        work_id="work-default-deny",
        task_id="task-default-deny",
        status=ExecutionStatus.FAILED,
    )
    manager.execution_registry.create(source)

    with pytest.raises(
        ValueError,
        match="Execution is not declared safe to retry",
    ):
        manager.admit_retry(
            source.execution_id,
            operation_id="retry-default-deny",
        )

    assert manager.execution_registry.list_by_task(
        source.task_id
    ) == [source]


@pytest.mark.parametrize(
    "status",
    (
        ExecutionStatus.QUEUED,
        ExecutionStatus.RUNNING,
        ExecutionStatus.PAUSED,
        ExecutionStatus.COMPLETED,
        ExecutionStatus.CANCELLED,
    ),
)
def test_manager_denies_nonretryable_terminal_and_active_states(
    status,
):
    manager = ShujaaManager(
        crew_runner=NeverStartedRunner()
    )
    source = Execution(
        execution_id=f"exec-denied-{status.value}",
        work_id="work-denied",
        task_id=f"task-denied-{status.value}",
        status=status,
        retry_safety=RetrySafety.DECLARED_SAFE,
    )
    manager.execution_registry.create(source)

    with pytest.raises(
        ValueError,
        match=(
            "Execution status is not retryable: "
            f"{status.value}"
        ),
    ):
        manager.admit_retry(
            source.execution_id,
            operation_id=f"retry-denied-{status.value}",
        )

    assert manager.execution_registry.list_by_task(
        source.task_id
    ) == [source]


@pytest.mark.parametrize(
    "status",
    (
        ExecutionStatus.FAILED,
        ExecutionStatus.TIMED_OUT,
    ),
)
def test_manager_admits_declared_safe_failed_or_timed_out(
    status,
):
    manager = ShujaaManager(
        crew_runner=NeverStartedRunner()
    )
    source = Execution(
        execution_id=f"exec-allowed-{status.value}",
        work_id="work-allowed",
        task_id=f"task-allowed-{status.value}",
        status=status,
        retry_safety=RetrySafety.DECLARED_SAFE,
        requested_agent_id="agent-original",
        required_capability="analysis",
    )
    manager.execution_registry.create(source)

    result = manager.admit_retry(
        source.execution_id,
        operation_id=f"retry-allowed-{status.value}",
    )

    assert result.applied is True
    assert result.execution.status == ExecutionStatus.QUEUED
    assert result.execution.previous_execution_id == (
        source.execution_id
    )
    assert result.execution.attempt_number == 2


def test_submit_rejects_untyped_retry_safety_before_dispatch():
    class NeverDispatched:
        def dispatch(self, request):
            raise AssertionError(
                "Invalid retry safety must fail before dispatch."
            )

    manager = ShujaaManager(
        crew_runner=NeverStartedRunner(),
        execution_dispatcher=NeverDispatched(),
    )

    with pytest.raises(
        ValueError,
        match="Retry safety must be a RetrySafety value",
    ):
        manager.submit(
            "invalid retry declaration",
            retry_safety="declared_safe",
        )


@pytest.mark.parametrize(
    "protected_change",
    (
        {"retry_safety": RetrySafety.DECLARED_SAFE},
        {"attempt_number": 2},
        {"previous_execution_id": "exec-forged-parent"},
        {"retry_operation_id": "retry-forged"},
        {"requested_agent_id": "agent-forged"},
        {"required_capability": "forged-capability"},
    ),
)
def test_save_rejects_retry_contract_mutation(
    protected_change,
):
    from dataclasses import replace

    registry = InMemoryExecutionRegistry()
    execution = Execution(
        execution_id="exec-protected-retry-contract",
        work_id="work-protected",
        task_id="task-protected",
    )
    registry.create(execution)

    bypass_attempt = replace(
        execution,
        **protected_change,
    )

    with pytest.raises(
        ValueError,
        match="State changes require transition",
    ):
        registry.save(bypass_attempt)

    assert registry.get(execution.execution_id) == execution


def test_manager_retry_replay_and_conflict_keep_one_attempt():
    manager = ShujaaManager(
        crew_runner=NeverStartedRunner()
    )
    source = Execution(
        execution_id="exec-manager-replay-source",
        work_id="work-manager-replay",
        task_id="task-manager-replay",
        status=ExecutionStatus.FAILED,
        retry_safety=RetrySafety.DECLARED_SAFE,
    )
    manager.execution_registry.create(source)

    first = manager.admit_retry(
        source.execution_id,
        operation_id="retry-manager-shared",
    )
    replay = manager.admit_retry(
        source.execution_id,
        operation_id="retry-manager-shared",
    )
    conflict = manager.admit_retry(
        source.execution_id,
        operation_id="retry-manager-conflict",
    )

    assert first.disposition.value == "applied"
    assert replay.disposition.value == "idempotent_replay"
    assert conflict.disposition.value == "conflicting_retry"
    assert replay.execution == first.execution
    assert conflict.execution == first.execution
    assert len(
        manager.execution_registry.list_by_task(
            source.task_id
        )
    ) == 2
