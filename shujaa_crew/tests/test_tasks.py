from __future__ import annotations

from uuid import uuid4

import pytest

from core.manager.service import ShujaaManager
from core.policy.contracts import (
    ActorRef,
    AuthorizationContext,
    AuthorizationRequest,
    ResourceRef,
)
from core.policy.evaluator import (
    SinglePrincipalCancelEvaluator,
    SinglePrincipalSubmitEvaluator,
)
from core.work.models import ExecutionStatus


class FakeProcess:
    pid = 12345

    def wait(self) -> int:
        return 0


class FakeRunner:
    def start(self, topic: str) -> FakeProcess:
        assert topic == "test task"
        return FakeProcess()


_CANCEL_ACTOR = ActorRef(
    actor_type="service",
    actor_id="test-tasks-local-api",
)


def _authorized_submit(manager, command, **kwargs):
    operation_id = f"op-test-tasks-submit-{uuid4()}"
    manager.submit_authorization_evaluator = (
        SinglePrincipalSubmitEvaluator(
            principal=_CANCEL_ACTOR,
            policy_version="test-tasks-submit-v1",
        )
    )
    return manager.submit(
        command,
        authorization_request=AuthorizationRequest(
            actor=_CANCEL_ACTOR,
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
            policy_version="test-tasks-cancel-v1",
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


def test_manager_creates_trackable_task():
    manager = ShujaaManager(crew_runner=FakeRunner())

    result = _authorized_submit(manager, "test task")
    task = manager.get_task(result["task_id"])

    assert result["status"] == "accepted"
    assert result["process_id"] == 12345
    assert task is not None
    assert task["command"] == "test task"
    assert task["status"] in {"running", "completed"}


def test_manager_reports_llm_quota_exhausted(tmp_path):
    class FakeProcess:
        pid = 12345

        def wait(self, timeout=None):
            return 1

    class FakeRunner:
        def __init__(self):
            self.log_path = tmp_path / "fake.log"
            self.log_path.write_text(
                "429 RESOURCE_EXHAUSTED",
                encoding="utf-8",
            )

        def start(self, topic: str):
            return FakeProcess()

        def get_error(self, return_code: int) -> str:
            return "LLM quota exhausted: RESOURCE_EXHAUSTED (429)."

    manager = ShujaaManager(crew_runner=FakeRunner())

    result = _authorized_submit(manager, "test task")

    import time
    time.sleep(0.1)

    task = manager.get_task(result["task_id"])

    assert task is not None
    assert task["status"] == "failed"
    assert task["error"] == (
        "LLM quota exhausted: RESOURCE_EXHAUSTED (429)."
    )


def test_manager_reports_meaningful_general_error(tmp_path):
    class FakeProcess:
        pid = 12345

        def wait(self, timeout=None):
            return 1

    class FakeRunner:
        def __init__(self):
            self.log_path = tmp_path / "fake-general-error.log"
            self.log_path.write_text(
                "Starting task\n"
                "Connection reset by peer\n"
                "Final error: external service failed\n",
                encoding="utf-8",
            )

        def start(self, topic: str):
            return FakeProcess()

        def get_error(self, return_code: int) -> str:
            return "Final error: external service failed"

    manager = ShujaaManager(crew_runner=FakeRunner())

    result = _authorized_submit(manager, "test task")

    import time
    time.sleep(0.1)

    task = manager.get_task(result["task_id"])

    assert task is not None
    assert task["status"] == "failed"
    assert task["error"] == "Final error: external service failed"


def test_manager_cancels_running_task():
    class FakeProcess:
        pid = 12345

        def wait(self, timeout=None):
            import time
            time.sleep(1)
            return 0

    class FakeRunner:
        def start(self, topic: str):
            return FakeProcess()

    manager = ShujaaManager(crew_runner=FakeRunner())

    result = _authorized_submit(manager, "test task")
    task_id = result["task_id"]

    task = manager.get_task(task_id)
    assert task is not None

    # الاختبار الوهمي يستخدم PID غير حقيقي، لذلك نلغي
    # الاعتماد على مجموعة عملية حقيقية.
    manager.task_store.update(
        task_id,
        status="running",
        process_group_id=None,
    )

    cancelled = _authorized_cancel(
        manager,
        task_id,
        cancel_operation_id="op-test-cancel-request-test_tasks-1",
        cleanup_operation_id="op-test-cancel-running",
    )

    assert cancelled["status"] == "cancelled"
    assert cancelled["error"] == "Task cancelled by user."


def test_cancelled_task_is_not_overwritten_after_process_exit():
    import threading
    import time

    release_process = threading.Event()

    class FakeProcess:
        pid = 987654321

        def wait(self, timeout=None):
            release_process.wait(timeout=1)
            return 1

    class FakeRunner:
        def start(self, topic: str):
            return FakeProcess()

    manager = ShujaaManager(crew_runner=FakeRunner())

    result = _authorized_submit(manager, "test cancellation race")
    task_id = result["task_id"]

    cancelled = _authorized_cancel(
        manager,
        task_id,
        cancel_operation_id="op-test-cancel-request-test_tasks-2",
        cleanup_operation_id="op-test-cancel-race",
    )
    assert cancelled["status"] == "cancelled"

    release_process.set()
    time.sleep(0.1)

    final_task = manager.get_task(task_id)

    assert final_task is not None
    assert final_task["status"] == "cancelled"
    assert final_task["error"] == "Task cancelled by user."


def test_cancel_uses_sigkill_if_process_group_survives(monkeypatch):
    import signal
    import core.manager.service as service_module

    sent_signals = []

    def fake_killpg(process_group_id, sig):
        sent_signals.append((process_group_id, sig))

        if len(sent_signals) == 3 and sig == 0:
            raise ProcessLookupError

    monkeypatch.setattr(service_module.os, "killpg", fake_killpg)

    class FakeRunner:
        def start(self, topic: str):
            raise NotImplementedError

        def get_error(self, return_code: int) -> str:
            return f"Exit code: {return_code}"

    manager = ShujaaManager(crew_runner=FakeRunner())
    manager.TERMINATION_GRACE_SECONDS = 0

    manager._terminate_process_group_by_id(12345)

    assert sent_signals == [
        (12345, signal.SIGTERM),
        (12345, signal.SIGKILL),
        (12345, 0),
    ]


def test_task_store_updates_result():
    from core.tasks.store import TaskRecord, TaskStore

    store = TaskStore()

    store.create(
        TaskRecord(
            task_id="result-test",
            command="test",
            status="running",
        )
    )

    store.update(
        "result-test",
        status="completed",
        result="Mock final result",
    )

    task = store.get("result-test")

    assert task is not None
    assert task.status == "completed"
    assert task.result == "Mock final result"
    assert task.to_dict()["result"] == "Mock final result"


def test_manager_stores_completed_runner_result():
    import time

    class ResultProcess:
        pid = 987654320

        def wait(self, timeout=None):
            return 0

    class ResultRunner:
        def start(self, topic: str):
            assert topic == "test result"
            return ResultProcess()

        def get_result(self, process):
            return "Mock task completed"

    manager = ShujaaManager(crew_runner=ResultRunner())

    submitted = _authorized_submit(manager, "test result")
    task_id = submitted["task_id"]

    deadline = time.monotonic() + 1.0
    task = None

    while time.monotonic() < deadline:
        task = manager.get_task(task_id)

        if task is not None and task["status"] == "completed":
            break

        time.sleep(0.01)

    assert task is not None
    assert task["status"] == "completed"
    assert task["result"] == "Mock task completed"


def test_manager_creates_work_before_task():
    manager = ShujaaManager(crew_runner=FakeRunner())

    result = _authorized_submit(manager, "test task")

    work_id = result["work_id"]
    task = manager.get_task(result["task_id"])
    work = manager.work_registry.get(work_id)

    assert isinstance(work_id, str)
    assert work_id.startswith("work-")
    assert work is not None
    assert work.request == "test task"

    assert task is not None
    assert task["work_id"] == work_id


def test_manager_creates_execution_before_runner():
    manager = ShujaaManager(crew_runner=FakeRunner())

    result = _authorized_submit(manager, "test task")

    execution_id = result["execution_id"]
    execution = manager.execution_registry.get(execution_id)

    assert isinstance(execution_id, str)
    assert execution_id.startswith("exec-")
    assert execution is not None
    assert execution.work_id == result["work_id"]
    assert execution.task_id == result["task_id"]


def test_manager_routes_execution_through_dispatcher():
    from core.work.dispatcher import DispatchDecision

    class RecordingDispatcher:
        def __init__(self):
            self.request = None

        def dispatch(self, request):
            self.request = request
            return DispatchDecision(
                executor_id="runner-test",
                runtime_id="test-runtime",
            )

    dispatcher = RecordingDispatcher()

    manager = ShujaaManager(
        crew_runner=FakeRunner(),
        execution_dispatcher=dispatcher,
    )

    result = _authorized_submit(manager, "test task")

    assert dispatcher.request is not None
    assert dispatcher.request.work_id == result["work_id"]
    assert dispatcher.request.task_id == result["task_id"]
    assert dispatcher.request.execution_id == result["execution_id"]

    execution = manager.execution_registry.get(
        result["execution_id"]
    )

    assert execution is not None
    assert execution.executor_id == "runner-test"


def test_manager_marks_execution_completed():
    import time

    manager = ShujaaManager(crew_runner=FakeRunner())

    result = _authorized_submit(manager, "test task")

    deadline = time.monotonic() + 1.0
    execution = None

    while time.monotonic() < deadline:
        execution = manager.execution_registry.get(
            result["execution_id"]
        )

        if (
            execution is not None
            and execution.status.value == "completed"
        ):
            break

        time.sleep(0.01)

    assert execution is not None
    assert execution.status.value == "completed"


def test_manager_marks_execution_failed():
    import time

    class FailedProcess:
        pid = 12345

        def wait(self, timeout=None):
            return 1

    class FailedRunner:
        def start(self, topic: str):
            return FailedProcess()

        def get_error(self, return_code: int) -> str:
            return "Test failure"

    manager = ShujaaManager(crew_runner=FailedRunner())

    result = _authorized_submit(manager, "test failure")

    deadline = time.monotonic() + 1.0
    execution = None

    while time.monotonic() < deadline:
        execution = manager.execution_registry.get(
            result["execution_id"]
        )

        if (
            execution is not None
            and execution.status.value == "failed"
        ):
            break

        time.sleep(0.01)

    assert execution is not None
    assert execution.status.value == "failed"


def test_manager_marks_execution_cancelled():
    import threading
    import time

    release_process = threading.Event()

    class SlowProcess:
        pid = 987654321

        def wait(self, timeout=None):
            release_process.wait(timeout=1)
            return 1

    class SlowRunner:
        def start(self, topic: str):
            return SlowProcess()

    manager = ShujaaManager(crew_runner=SlowRunner())

    result = _authorized_submit(manager, "cancel execution")
    task_id = result["task_id"]
    execution_id = result["execution_id"]

    _authorized_cancel(
        manager,
        task_id,
        cancel_operation_id="op-test-cancel-request-test_tasks-3",
        cleanup_operation_id="op-test-cancel-execution",
    )

    release_process.set()

    deadline = time.monotonic() + 1.0
    execution = None

    while time.monotonic() < deadline:
        execution = manager.execution_registry.get(execution_id)

        if (
            execution is not None
            and execution.status.value == "cancelled"
        ):
            break

        time.sleep(0.01)

    assert execution is not None
    assert execution.status.value == "cancelled"


def test_manager_marks_execution_timed_out(monkeypatch):
    import subprocess
    import time

    class TimeoutProcess:
        pid = 987654322

        def wait(self, timeout=None):
            raise subprocess.TimeoutExpired(
                cmd="test",
                timeout=timeout,
            )

    class TimeoutRunner:
        def start(self, topic: str):
            return TimeoutProcess()

    manager = ShujaaManager(crew_runner=TimeoutRunner())

    monkeypatch.setattr(
        manager,
        "_terminate_process_group",
        lambda process, process_group_id: None,
    )

    result = _authorized_submit(manager, "timeout execution")

    deadline = time.monotonic() + 1.0
    execution = None

    while time.monotonic() < deadline:
        execution = manager.execution_registry.get(
            result["execution_id"]
        )

        if (
            execution is not None
            and execution.status.value == "timed_out"
        ):
            break

        time.sleep(0.01)

    assert execution is not None
    assert execution.status.value == "timed_out"


def test_manager_passes_requested_agent_to_dispatcher():
    from core.work.dispatcher import DispatchDecision

    class RecordingDispatcher:
        def __init__(self):
            self.request = None

        def dispatch(self, request):
            self.request = request
            return DispatchDecision(
                executor_id="research-agent",
                agent_id="research-agent",
                runtime_id="agent-executor",
            )

    dispatcher = RecordingDispatcher()

    manager = ShujaaManager(
        crew_runner=FakeRunner(),
        execution_dispatcher=dispatcher,
    )

    result = _authorized_submit(
        manager,
        "test task",
        requested_agent_id="research-agent",
    )

    assert dispatcher.request is not None
    assert (
        dispatcher.request.requested_agent_id
        == "research-agent"
    )

    execution = manager.execution_registry.get(
        result["execution_id"]
    )

    assert execution is not None
    assert execution.executor_id == "research-agent"


def test_manager_accepts_agent_runtime_dependencies():
    from core.agents.executor_registry import AgentExecutorRegistry
    from core.agents.registry import InMemoryAgentRegistry

    agent_registry = InMemoryAgentRegistry()
    executor_registry = AgentExecutorRegistry()

    manager = ShujaaManager(
        crew_runner=FakeRunner(),
        agent_registry=agent_registry,
        agent_executor_registry=executor_registry,
    )

    assert manager.agent_registry is agent_registry
    assert manager.agent_executor_registry is executor_registry


def test_manager_executes_agent_without_using_runner():
    import time

    from core.agents.executor_registry import AgentExecutorRegistry
    from core.agents.models import AgentDefinition
    from core.agents.registry import InMemoryAgentRegistry

    class ForbiddenRunner:
        def start(self, topic: str):
            raise AssertionError(
                "Runner must not execute an agent-routed task."
            )

    class FakeAgentExecutor:
        def execute(self, agent, task):
            return f"{agent.agent_id}:{task}"

    agent_registry = InMemoryAgentRegistry()

    agent_registry.register(
        AgentDefinition(
            agent_id="research-agent",
            name="Research Agent",
            description="Researches information.",
            capabilities=("research",),
            executor="mock",
        )
    )

    executor_registry = AgentExecutorRegistry()
    executor_registry.register(
        "research-agent",
        FakeAgentExecutor(),
    )

    manager = ShujaaManager(
        crew_runner=ForbiddenRunner(),
        agent_registry=agent_registry,
        agent_executor_registry=executor_registry,
    )

    result = _authorized_submit(
        manager,
        "research this",
        requested_agent_id="research-agent",
    )

    deadline = time.monotonic() + 1.0
    task = None

    while time.monotonic() < deadline:
        task = manager.get_task(result["task_id"])

        if task is not None and task["status"] == "completed":
            break

        time.sleep(0.01)

    execution = manager.execution_registry.get(
        result["execution_id"]
    )

    assert task is not None
    assert task["status"] == "completed"
    assert task["result"] == "research-agent:research this"

    assert execution is not None
    assert execution.work_id == result["work_id"]
    assert execution.task_id == result["task_id"]
    assert execution.executor_id == "research-agent"
    assert execution.status == ExecutionStatus.COMPLETED


def test_manager_passes_required_capability_to_dispatcher():
    from core.work.dispatcher import DispatchDecision

    class RecordingDispatcher:
        def __init__(self):
            self.request = None

        def dispatch(self, request):
            self.request = request
            return DispatchDecision(
                executor_id="runner-test",
                runtime_id="process-runner",
            )

    dispatcher = RecordingDispatcher()

    manager = ShujaaManager(
        crew_runner=FakeRunner(),
        execution_dispatcher=dispatcher,
    )

    _authorized_submit(
        manager,
        "research this",
        required_capability="research",
    )

    assert dispatcher.request is not None
    assert dispatcher.request.required_capability == "research"


def test_manager_executes_agent_by_required_capability():
    import time

    from core.agents.executor_registry import AgentExecutorRegistry
    from core.agents.models import AgentDefinition
    from core.agents.registry import InMemoryAgentRegistry

    class ForbiddenRunner:
        def start(self, topic: str):
            raise AssertionError(
                "Runner must not execute capability-routed task."
            )

    class FakeAgentExecutor:
        def execute(self, agent, task):
            return f"{agent.agent_id}:{task}"

    agent_registry = InMemoryAgentRegistry()
    agent_registry.register(
        AgentDefinition(
            agent_id="analysis-agent",
            name="Analysis Agent",
            description="Analyzes information.",
            capabilities=("analysis",),
        )
    )

    executor_registry = AgentExecutorRegistry()
    executor_registry.register(
        "analysis-agent",
        FakeAgentExecutor(),
    )

    manager = ShujaaManager(
        crew_runner=ForbiddenRunner(),
        agent_registry=agent_registry,
        agent_executor_registry=executor_registry,
    )

    submitted = _authorized_submit(
        manager,
        "analyze this",
        required_capability="analysis",
    )

    deadline = time.monotonic() + 1.0
    task = None

    while time.monotonic() < deadline:
        task = manager.get_task(submitted["task_id"])

        if task is not None and task["status"] == "completed":
            break

        time.sleep(0.01)

    assert task is not None
    assert task["status"] == "completed"
    assert task["result"] == "analysis-agent:analyze this"


def test_manager_rejects_agent_without_executor():
    from core.agents.executor_registry import AgentExecutorRegistry
    from core.agents.models import AgentDefinition
    from core.agents.registry import InMemoryAgentRegistry

    agent_registry = InMemoryAgentRegistry()
    agent_registry.register(
        AgentDefinition(
            agent_id="agent-without-executor",
            name="Agent",
            description="No executor.",
            capabilities=("test",),
        )
    )

    manager = ShujaaManager(
        crew_runner=FakeRunner(),
        agent_registry=agent_registry,
        agent_executor_registry=AgentExecutorRegistry(),
    )

    with pytest.raises(
        ValueError,
        match="No executor registered for capability: test",
    ):
        _authorized_submit(
            manager,
            "test task",
            required_capability="test",
        )
