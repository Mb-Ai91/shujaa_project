from core.tasks.store import TaskRecord
from core.work.models import (
    Execution,
    ExecutionStatus,
    Work,
    WorkStatus,
    new_execution_id,
    new_work_id,
)


def test_work_has_traceable_identity():
    work_id = new_work_id()

    work = Work(
        work_id=work_id,
        request="Perform a test task.",
    )

    assert work.work_id == work_id
    assert work.work_id.startswith("work-")
    assert work.status == WorkStatus.QUEUED


def test_execution_has_traceable_identity():
    execution_id = new_execution_id()

    execution = Execution(
        execution_id=execution_id,
        work_id="work-123",
        task_id="task-123",
    )

    assert execution.execution_id == execution_id
    assert execution.execution_id.startswith("exec-")
    assert execution.work_id == "work-123"
    assert execution.task_id == "task-123"
    assert execution.status == ExecutionStatus.QUEUED


def test_work_task_execution_relationship_is_traceable():
    work_id = new_work_id()

    work = Work(
        work_id=work_id,
        request="Perform linked work.",
    )

    task = TaskRecord(
        task_id="task-123",
        work_id=work_id,
        command="Perform linked task.",
        status="queued",
    )

    execution = Execution(
        execution_id=new_execution_id(),
        work_id=work_id,
        task_id=task.task_id,
    )

    assert task.work_id == work.work_id
    assert execution.work_id == work.work_id
    assert execution.task_id == task.task_id


def test_work_and_execution_metadata_are_independent():
    work = Work(
        work_id=new_work_id(),
        request="Test",
    )

    execution = Execution(
        execution_id=new_execution_id(),
        work_id=work.work_id,
        task_id="task-123",
    )

    work.metadata["source"] = "user"

    assert execution.metadata == {}


def test_work_supports_pending_approval_state():
    work = Work(
        work_id=new_work_id(),
        request="Requires approval.",
        status=WorkStatus.PENDING_APPROVAL,
    )

    assert work.status == WorkStatus.PENDING_APPROVAL
