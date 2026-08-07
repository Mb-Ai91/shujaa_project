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

    manager = ShujaaManager(crew_runner=FakeRunner())

    result = manager.submit("test task")

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

    manager = ShujaaManager(crew_runner=FakeRunner())

    result = manager.submit("test task")

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

    result = manager.submit("test task")
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

    cancelled = manager.cancel_task(task_id)

    assert cancelled["status"] == "cancelled"
    assert cancelled["error"] == "Task cancelled by user."
