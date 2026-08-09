from core.tasks.store import TaskRecord
from core.work.models import (
    Execution,
    ExecutionStatus,
    Work,
    WorkStatus,
    new_execution_id,
    new_work_id,
    utc_now,
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


def test_work_defaults_to_zero_progress():
    work = Work(
        work_id=new_work_id(),
        request="Track progress.",
    )

    assert work.progress == 0.0
    assert work.queue_position is None


def test_work_can_record_progress_and_queue_position():
    work = Work(
        work_id=new_work_id(),
        request="Queued work.",
        progress=0.5,
        queue_position=3,
    )

    assert work.progress == 0.5
    assert work.queue_position == 3


def test_work_can_reference_parent_work():
    parent_id = new_work_id()

    child = Work(
        work_id=new_work_id(),
        request="Child work.",
        parent_work_id=parent_id,
    )

    assert child.parent_work_id == parent_id


def test_work_can_record_dependencies():
    dependency_1 = new_work_id()
    dependency_2 = new_work_id()

    work = Work(
        work_id=new_work_id(),
        request="Dependent work.",
        dependency_work_ids=(
            dependency_1,
            dependency_2,
        ),
    )

    assert work.dependency_work_ids == (
        dependency_1,
        dependency_2,
    )


def test_work_relationships_default_to_independent():
    work = Work(
        work_id=new_work_id(),
        request="Independent work.",
    )

    assert work.parent_work_id is None
    assert work.dependency_work_ids == ()


def test_work_can_record_result():
    work = Work(
        work_id=new_work_id(),
        request="Produce a result.",
        result="Completed result.",
    )

    assert work.result == "Completed result."


def test_work_can_reference_artifacts():
    work = Work(
        work_id=new_work_id(),
        request="Produce artifacts.",
        artifact_refs=(
            "artifact-report",
            "artifact-data",
        ),
    )

    assert work.artifact_refs == (
        "artifact-report",
        "artifact-data",
    )


def test_work_result_and_artifacts_default_to_empty():
    work = Work(
        work_id=new_work_id(),
        request="No output yet.",
    )

    assert work.result is None
    assert work.artifact_refs == ()


def test_work_can_record_deadline_and_sla():
    deadline = utc_now()

    work = Work(
        work_id=new_work_id(),
        request="Time-bound work.",
        deadline_at=deadline,
        sla_seconds=300,
    )

    assert work.deadline_at == deadline
    assert work.sla_seconds == 300


def test_work_deadline_and_sla_default_to_none():
    work = Work(
        work_id=new_work_id(),
        request="Untimed work.",
    )

    assert work.deadline_at is None
    assert work.sla_seconds is None


def test_work_can_reference_events():
    work = Work(
        work_id=new_work_id(),
        request="Traceable work.",
        event_refs=(
            "event-1",
            "event-2",
        ),
    )

    assert work.event_refs == (
        "event-1",
        "event-2",
    )


def test_work_event_refs_default_to_empty():
    work = Work(
        work_id=new_work_id(),
        request="No events yet.",
    )

    assert work.event_refs == ()
