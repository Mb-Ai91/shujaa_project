import pytest
from uuid import uuid4

from core.manager.service import ShujaaManager
from core.policy.contracts import (
    ActorRef,
    AuthorizationContext,
    AuthorizationRequest,
    ResourceRef,
)
from core.policy.evaluator import SinglePrincipalSubmitEvaluator
from core.work.execution_registry import (
    InMemoryExecutionRegistry,
)
from core.work.models import (
    Execution,
    ExecutionStatus,
    RetrySafety,
)


_SUBMIT_ACTOR = ActorRef(
    actor_type="service",
    actor_id="test-retry-admission-submit",
)


def _authorized_submit(manager, command, **kwargs):
    operation_id = f"op-test-retry-submit-{uuid4()}"
    manager.submit_authorization_evaluator = (
        SinglePrincipalSubmitEvaluator(
            principal=_SUBMIT_ACTOR,
            policy_version="test-retry-admission-submit-v1",
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

    submitted = _authorized_submit(
        manager,
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
        _authorized_submit(
            manager,
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


def test_retry_dispatch_rejection_creates_no_partial_attempt():
    from core.tasks.store import TaskRecord

    class RejectingDispatcher:
        def __init__(self):
            self.request = None

        def dispatch(self, request):
            self.request = request
            raise ValueError("retry route rejected")

    dispatcher = RejectingDispatcher()
    manager = ShujaaManager(
        crew_runner=NeverStartedRunner(),
        execution_dispatcher=dispatcher,
    )
    task = TaskRecord(
        task_id="task-retry-dispatch-rejected",
        work_id="work-retry-dispatch-rejected",
        command="retry this task",
        status="failed",
        error="original failure",
    )
    source = Execution(
        execution_id="exec-retry-dispatch-source",
        work_id=task.work_id,
        task_id=task.task_id,
        status=ExecutionStatus.FAILED,
        retry_safety=RetrySafety.DECLARED_SAFE,
        requested_agent_id="agent-original",
        required_capability="analysis",
    )
    manager.task_store.create(task)
    manager.execution_registry.create(source)

    with pytest.raises(
        ValueError,
        match="retry route rejected",
    ):
        manager.retry_task(
            source.execution_id,
            operation_id="retry-dispatch-operation",
        )

    assert dispatcher.request is not None
    assert dispatcher.request.work_id == source.work_id
    assert dispatcher.request.task_id == source.task_id
    assert (
        dispatcher.request.execution_id
        != source.execution_id
    )
    assert dispatcher.request.command == task.command
    assert (
        dispatcher.request.requested_agent_id
        == source.requested_agent_id
    )
    assert (
        dispatcher.request.required_capability
        == source.required_capability
    )
    assert manager.execution_registry.list_by_task(
        source.task_id
    ) == [source]

    unchanged = manager.task_store.get(task.task_id)

    assert unchanged is not None
    assert unchanged.status == "failed"
    assert unchanged.error == "original failure"


def test_retry_dispatch_hands_off_winning_attempt_to_runtime():
    import time

    from core.tasks.store import TaskRecord
    from core.work.dispatcher import DispatchDecision

    class RetryProcess:
        pid = 12345

        def wait(self, timeout=None):
            return 0

    class RetryRunner:
        def __init__(self):
            self.commands = []

        def start(self, command):
            self.commands.append(command)
            return RetryProcess()

        def get_result(self, process):
            return "retry completed"

    class RetryDispatcher:
        def __init__(self):
            self.request = None
            self.calls = 0

        def dispatch(self, request):
            self.request = request
            self.calls += 1
            return DispatchDecision(
                executor_id="retry-executor",
                runtime_id="process-runner",
            )

    runner = RetryRunner()
    dispatcher = RetryDispatcher()
    manager = ShujaaManager(
        crew_runner=runner,
        execution_dispatcher=dispatcher,
    )
    task = TaskRecord(
        task_id="task-retry-runtime",
        work_id="work-retry-runtime",
        command="retry runtime task",
        status="failed",
        error="original failure",
    )
    source = Execution(
        execution_id="exec-retry-runtime-source",
        work_id=task.work_id,
        task_id=task.task_id,
        status=ExecutionStatus.FAILED,
        retry_safety=RetrySafety.DECLARED_SAFE,
    )
    manager.task_store.create(task)
    manager.execution_registry.create(source)

    admission = manager.retry_task(
        source.execution_id,
        operation_id="retry-runtime-operation",
    )

    assert admission.applied is True
    assert (
        admission.execution.executor_id
        == "retry-executor"
    )

    deadline = time.monotonic() + 1.0
    retry = None

    while time.monotonic() < deadline:
        retry = manager.execution_registry.get(
            admission.execution.execution_id
        )

        if (
            retry is not None
            and retry.status == ExecutionStatus.COMPLETED
        ):
            break

        time.sleep(0.01)

    replay = manager.retry_task(
        source.execution_id,
        operation_id="retry-runtime-operation",
    )
    conflict = manager.retry_task(
        source.execution_id,
        operation_id="retry-runtime-conflict",
    )

    original = manager.execution_registry.get(
        source.execution_id
    )
    updated_task = manager.task_store.get(task.task_id)

    assert dispatcher.request is not None
    assert dispatcher.calls == 1
    assert runner.commands == ["retry runtime task"]
    assert replay.disposition.value == "idempotent_replay"
    assert conflict.disposition.value == "conflicting_retry"
    assert (
        replay.execution.execution_id
        == admission.execution.execution_id
    )
    assert (
        conflict.execution.execution_id
        == admission.execution.execution_id
    )
    assert replay.execution == retry
    assert conflict.execution == retry
    assert original == source
    assert retry is not None
    assert retry.status == ExecutionStatus.COMPLETED
    assert retry.result == "retry completed"
    assert retry.previous_execution_id == source.execution_id
    assert retry.attempt_number == 2
    assert updated_task is not None
    assert updated_task.status == "completed"
    assert updated_task.error is None
    assert updated_task.result == "retry completed"
