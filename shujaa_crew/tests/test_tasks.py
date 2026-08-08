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

    result = manager.submit("test cancellation race")
    task_id = result["task_id"]

    cancelled = manager.cancel_task(task_id)
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

    monkeypatch.setattr(service_module.os, "killpg", fake_killpg)

    manager = ShujaaManager()
    manager.TERMINATION_GRACE_SECONDS = 0

    manager._terminate_process_group_by_id(12345)

    assert sent_signals == [
        (12345, signal.SIGTERM),
        (12345, signal.SIGKILL),
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

    submitted = manager.submit("test result")
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
