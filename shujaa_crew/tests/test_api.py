from __future__ import annotations

import os
from uuid import uuid4

import pytest

from apps.api.app import app
from core.manager.service import ShujaaManager
from core.policy.contracts import (
    ActorRef,
    AuthorizationContext,
    AuthorizationRequest,
    ResourceRef,
)
from core.policy.evaluator import SinglePrincipalSubmitEvaluator


_SUBMIT_ACTOR = ActorRef(
    actor_type="service",
    actor_id="test-api-submit",
)


def _authorized_submit(manager, command, **kwargs):
    operation_id = f"op-test-api-submit-{uuid4()}"
    manager.submit_authorization_evaluator = (
        SinglePrincipalSubmitEvaluator(
            principal=_SUBMIT_ACTOR,
            policy_version="test-api-submit-v1",
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


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("SHUJAA_API_KEY", "test-secret-key")
    app.config["TESTING"] = True

    with app.test_client() as test_client:
        yield test_client


def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {
        "service": "shujaa-api",
        "status": "healthy",
    }


def test_task_requires_api_key(client):
    response = client.post(
        "/shujaa-task",
        json={"command": "test"},
    )

    assert response.status_code == 401
    assert response.get_json()["message"] == "Unauthorized."


def test_task_rejects_invalid_json(client):
    response = client.post(
        "/shujaa-task",
        headers={"X-Shujaa-Key": "test-secret-key"},
        data="not-json",
        content_type="text/plain",
    )

    assert response.status_code == 400
    assert response.get_json()["message"] == "Invalid JSON payload."


def test_task_rejects_missing_command(client):
    response = client.post(
        "/shujaa-task",
        headers={"X-Shujaa-Key": "test-secret-key"},
        json={},
    )

    assert response.status_code == 400
    assert response.get_json()["message"] == "Command must be a string."


def test_manager_accepts_valid_command():
    class FakeProcess:
        pid = 12345

        def wait(self) -> int:
            return 0

    class FakeRunner:
        def start(self, topic: str) -> FakeProcess:
            assert topic == "test task"
            return FakeProcess()

    manager = ShujaaManager(crew_runner=FakeRunner())
    result = _authorized_submit(manager, " test task ")

    assert result["status"] == "accepted"
    assert result["process_id"] == 12345


def test_cancel_task_endpoint(monkeypatch):
    class FakeManager:
        def cancel_task(
            self,
            task_id: str,
            *,
            authorization_request,
            cancel_operation_id: str,
            cleanup_operation_id: str,
        ):
            assert task_id == "task-123"
            assert authorization_request.action == "task.cancel"
            assert authorization_request.resource.resource_id == task_id
            assert isinstance(cancel_operation_id, str)
            assert isinstance(cleanup_operation_id, str)
            assert cancel_operation_id != (
                cleanup_operation_id
            )
            return {
                "task_id": task_id,
                "status": "cancelled",
                "error": "Task cancelled by user.",
            }

    import apps.api.app as api_module

    monkeypatch.setattr(api_module, "manager", FakeManager())

    client = api_module.app.test_client()
    api_key = __import__("os").getenv("SHUJAA_API_KEY")

    response = client.post(
        "/tasks/task-123/cancel",
        headers={"X-Shujaa-Key": api_key},
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["status"] == "cancelled"
    assert data["task_id"] == "task-123"


def test_agents_endpoint_requires_api_key(client):
    response = client.get("/agents")

    assert response.status_code == 401


def test_agents_endpoint_returns_list(client):
    import os

    response = client.get(
        "/agents",
        headers={
            "X-Shujaa-Key": os.getenv("SHUJAA_API_KEY"),
        },
    )

    assert response.status_code == 200
    assert isinstance(response.get_json(), list)


def test_execute_agent_requires_api_key(client):
    response = client.post(
        "/agents/research-agent/execute",
        json={"task": "test"},
    )

    assert response.status_code == 401


def test_execute_agent_returns_mock_result(client):
    import os

    response = client.post(
        "/agents/research-agent/execute",
        headers={
            "X-Shujaa-Key": os.getenv("SHUJAA_API_KEY"),
        },
        json={
            "task": "research this topic",
        },
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["status"] == "completed"
    assert data["agent_id"] == "research-agent"
    assert data["result"] == (
        "Mock execution completed by "
        "research-agent: research this topic"
    )


def test_execute_unknown_agent_returns_404(client):
    import os

    response = client.post(
        "/agents/missing-agent/execute",
        headers={
            "X-Shujaa-Key": os.getenv("SHUJAA_API_KEY"),
        },
        json={
            "task": "test",
        },
    )

    assert response.status_code == 404
