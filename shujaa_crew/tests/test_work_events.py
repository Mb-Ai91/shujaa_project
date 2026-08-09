from core.work.events import WorkEvent, new_event_id


def test_event_has_traceable_identity():
    event = WorkEvent(
        event_id=new_event_id(),
        event_type="execution.started",
        entity_type="execution",
        entity_id="exec-123",
        work_id="work-123",
        task_id="task-123",
        execution_id="exec-123",
    )

    assert event.event_id.startswith("event-")
    assert event.event_type == "execution.started"
    assert event.entity_type == "execution"
    assert event.entity_id == "exec-123"
    assert event.work_id == "work-123"
    assert event.task_id == "task-123"
    assert event.execution_id == "exec-123"


def test_event_payload_is_independent():
    first = WorkEvent(
        event_id=new_event_id(),
        event_type="work.created",
        entity_type="work",
        entity_id="work-1",
    )

    second = WorkEvent(
        event_id=new_event_id(),
        event_type="work.created",
        entity_type="work",
        entity_id="work-2",
    )

    first.payload["source"] = "user"

    assert second.payload == {}


def test_event_can_record_actor_and_context():
    event = WorkEvent(
        event_id=new_event_id(),
        event_type="work.cancelled",
        entity_type="work",
        entity_id="work-123",
        work_id="work-123",
        actor_id="owner",
        payload={
            "reason": "Owner requested cancellation",
        },
    )

    assert event.actor_id == "owner"
    assert event.payload["reason"] == (
        "Owner requested cancellation"
    )
