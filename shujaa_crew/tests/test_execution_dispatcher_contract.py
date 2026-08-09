from core.work.dispatcher import (
    DispatchDecision,
    DispatchRequest,
)


def test_dispatch_request_preserves_execution_context():
    request = DispatchRequest(
        work_id="work-123",
        task_id="task-123",
        execution_id="exec-123",
        command="Perform the requested operation.",
        requested_agent_id="agent-research",
        required_capability="research",
    )

    assert request.work_id == "work-123"
    assert request.task_id == "task-123"
    assert request.execution_id == "exec-123"
    assert request.requested_agent_id == "agent-research"
    assert request.required_capability == "research"


def test_dispatch_decision_is_runtime_independent():
    decision = DispatchDecision(
        executor_id="executor-123",
        agent_id="agent-123",
        runtime_id="runtime-123",
    )

    assert decision.executor_id == "executor-123"
    assert decision.agent_id == "agent-123"
    assert decision.runtime_id == "runtime-123"
    assert decision.workflow_id is None
    assert decision.tool_id is None


def test_dispatch_contract_supports_future_routing_metadata():
    request = DispatchRequest(
        work_id="work-1",
        task_id="task-1",
        execution_id="exec-1",
        command="Future command type",
        metadata={
            "custom_requirement": "future-capability",
        },
    )

    decision = DispatchDecision(
        executor_id="executor-1",
        metadata={
            "routing_reason": "capability-match",
        },
    )

    assert request.metadata["custom_requirement"] == (
        "future-capability"
    )
    assert decision.metadata["routing_reason"] == (
        "capability-match"
    )


def test_dispatch_metadata_is_independent():
    first = DispatchRequest(
        work_id="work-1",
        task_id="task-1",
        execution_id="exec-1",
        command="First",
    )
    second = DispatchRequest(
        work_id="work-2",
        task_id="task-2",
        execution_id="exec-2",
        command="Second",
    )

    first.metadata["source"] = "manager"

    assert second.metadata == {}


def test_default_dispatcher_routes_to_current_runner():
    from core.work.dispatcher import DefaultExecutionDispatcher

    dispatcher = DefaultExecutionDispatcher()

    request = DispatchRequest(
        work_id="work-1",
        task_id="task-1",
        execution_id="exec-1",
        command="Run current task.",
    )

    decision = dispatcher.dispatch(request)

    assert decision.executor_id == "runner-default"
    assert decision.runtime_id == "process-runner"
    assert decision.agent_id is None
    assert decision.workflow_id is None
    assert decision.tool_id is None
    assert decision.metadata["route"] == "default-runner"


def test_default_dispatcher_routes_requested_agent():
    from core.agents.models import AgentDefinition
    from core.agents.registry import InMemoryAgentRegistry
    from core.work.dispatcher import DefaultExecutionDispatcher

    registry = InMemoryAgentRegistry()
    registry.register(
        AgentDefinition(
            agent_id="research-agent",
            name="Research Agent",
            description="Researches information.",
            capabilities=("research",),
            executor="mock",
        )
    )

    dispatcher = DefaultExecutionDispatcher(
        agent_registry=registry,
    )

    decision = dispatcher.dispatch(
        DispatchRequest(
            work_id="work-1",
            task_id="task-1",
            execution_id="exec-1",
            command="Research this.",
            requested_agent_id="research-agent",
        )
    )

    assert decision.agent_id == "research-agent"
    assert decision.executor_id == "research-agent"
    assert decision.runtime_id == "agent-executor"
    assert decision.metadata["route"] == "agent-executor"
    assert decision.metadata["executor_type"] == "mock"


def test_default_dispatcher_rejects_unknown_requested_agent():
    import pytest

    from core.agents.registry import InMemoryAgentRegistry
    from core.work.dispatcher import DefaultExecutionDispatcher

    dispatcher = DefaultExecutionDispatcher(
        agent_registry=InMemoryAgentRegistry(),
    )

    with pytest.raises(
        ValueError,
        match="Agent not found:",
    ):
        dispatcher.dispatch(
            DispatchRequest(
                work_id="work-1",
                task_id="task-1",
                execution_id="exec-1",
                command="Research this.",
                requested_agent_id="missing-agent",
            )
        )


def test_default_dispatcher_selects_runnable_agent_by_capability():
    from core.agents.executor_registry import AgentExecutorRegistry
    from core.agents.models import AgentDefinition
    from core.agents.registry import InMemoryAgentRegistry
    from core.work.dispatcher import (
        DefaultExecutionDispatcher,
        DispatchRequest,
    )

    class FakeExecutor:
        def execute(self, agent, task):
            return "done"

    registry = InMemoryAgentRegistry()

    registry.register(
        AgentDefinition(
            agent_id="unavailable-agent",
            name="Unavailable",
            description="Has no registered executor.",
            capabilities=("research",),
        )
    )

    registry.register(
        AgentDefinition(
            agent_id="runnable-agent",
            name="Runnable",
            description="Has a registered executor.",
            capabilities=("Research",),
        )
    )

    executor_registry = AgentExecutorRegistry()
    executor_registry.register(
        "runnable-agent",
        FakeExecutor(),
    )

    dispatcher = DefaultExecutionDispatcher(
        agent_registry=registry,
        agent_executor_registry=executor_registry,
    )

    decision = dispatcher.dispatch(
        DispatchRequest(
            work_id="work-1",
            task_id="task-1",
            execution_id="exec-1",
            command="research this",
            required_capability=" RESEARCH ",
        )
    )

    assert decision.agent_id == "runnable-agent"
    assert decision.executor_id == "runnable-agent"
    assert decision.runtime_id == "agent-executor"
    assert decision.metadata["selection"] == "capability"
