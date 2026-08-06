from __future__ import annotations

from core.manager.service import ShujaaManager


class FakeProcess:
    pid = 12345

    def wait(self) -> int:
        return 0


class FakeRunner:
    def start(self, topic: str) -> FakeProcess:
        assert topic == "test task"
        return FakeProcess()


def test_manager_creates_trackable_task():
    manager = ShujaaManager(crew_runner=FakeRunner())

    result = manager.submit("test task")
    task = manager.get_task(result["task_id"])

    assert result["status"] == "accepted"
    assert result["process_id"] == 12345
    assert task is not None
    assert task["command"] == "test task"
    assert task["status"] in {"running", "completed"}
