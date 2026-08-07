from __future__ import annotations

import os

import pytest

from apps.api.app import app
from core.manager.service import ShujaaManager


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
    result = manager.submit(" test task ")

    assert result["status"] == "accepted"
    assert result["process_id"] == 12345


def test_cancel_task_endpoint(monkeypatch):
    class FakeManager:
        def cancel_task(self, task_id: str):
            assert task_id == "task-123"
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
