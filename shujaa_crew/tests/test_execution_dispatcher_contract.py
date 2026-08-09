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
