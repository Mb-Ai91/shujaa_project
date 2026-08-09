from dataclasses import asdict, dataclass
from threading import Lock


@dataclass
class TaskRecord:
    task_id: str
    command: str
    status: str
    work_id: str | None = None
    process_id: int | None = None
    process_group_id: int | None = None
    error: str | None = None
    result: str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class InMemoryTaskStore:
    """مخزن مؤقت لحالات المهام داخل الذاكرة."""

    def __init__(self) -> None:
        self._tasks: dict[str, TaskRecord] = {}
        self._lock = Lock()

    def create(self, task: TaskRecord) -> None:
        with self._lock:
            self._tasks[task.task_id] = task

    def get(self, task_id: str) -> TaskRecord | None:
        with self._lock:
            return self._tasks.get(task_id)

    def update(
        self,
        task_id: str,
        *,
        status: str,
        process_id: int | None = None,
        process_group_id: int | None = None,
        error: str | None = None,
        result: str | None = None,
    ) -> None:
        with self._lock:
            task = self._tasks.get(task_id)

            if task is None:
                return

            task.status = status

            if process_id is not None:
                task.process_id = process_id

            if process_group_id is not None:
                task.process_group_id = process_group_id

            if error is not None:
                task.error = error

            if result is not None:
                task.result = result


# توافق مؤقت مع الاسم القديم أثناء الانتقال المعماري.
TaskStore = InMemoryTaskStore
