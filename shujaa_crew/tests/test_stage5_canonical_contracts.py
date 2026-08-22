from datetime import datetime, timedelta, timezone

import pytest

from core.work import events


UTC_TIME = datetime(
    2026,
    8,
    16,
    12,
    0,
    tzinfo=timezone.utc,
)


def make_event(**overrides):
    values = {
        "event_id": "event-1",
        "schema_version": "1",
        "event_type": "execution.started",
        "entity_type": "execution",
        "entity_id": "exec-1",
        "source_component": "core.manager",
        "correlation_id": "correlation-1",
        "occurred_at": UTC_TIME,
        "recorded_at": UTC_TIME,
        "work_id": "work-1",
        "task_id": "task-1",
        "execution_id": "exec-1",
        "operation_id": "operation-1",
        "payload": {"reason_code": "accepted"},
    }
    values.update(overrides)
    return events.WorkEvent(**values)


def make_audit(**overrides):
    values = {
        "audit_id": "audit-1",
        "schema_version": "1",
        "recorded_at": UTC_TIME,
        "action": "execution.start",
        "actor_type": "owner",
        "actor_id": "owner-1",
        "resource_type": "execution",
        "resource_id": "exec-1",
        "outcome": "accepted",
        "reason_code": "owner_request",
        "operation_id": "operation-1",
        "event_id": "event-1",
    }
    values.update(overrides)
    return events.AuditRecord(**values)


def test_event_v1_exposes_canonical_identity():
    event = make_event(
        actor_ref="owner-1",
        capability_asset_id="capability-research",
        resolved_adapter_id="adapter-local",
        resolved_adapter_version="1.0",
    )

    assert event.schema_version == "1"
    assert event.source_component == "core.manager"
    assert event.correlation_id == "correlation-1"
    assert event.operation_id == "operation-1"
    assert event.actor_ref == "owner-1"
    assert event.capability_asset_id == "capability-research"
    assert event.resolved_adapter_id == "adapter-local"
    assert event.resolved_adapter_version == "1.0"


def test_event_timestamps_are_utc():
    event = make_event()

    assert event.occurred_at.utcoffset() == timedelta(0)
    assert event.recorded_at.utcoffset() == timedelta(0)


def test_event_rejects_naive_timestamp():
    with pytest.raises(ValueError):
        make_event(
            occurred_at=datetime(2026, 8, 16, 12, 0),
        )


def test_event_rejects_recording_before_occurrence():
    with pytest.raises(ValueError):
        make_event(
            recorded_at=UTC_TIME - timedelta(seconds=1),
        )


@pytest.mark.parametrize(
    "field_name",
    (
        "event_id",
        "event_type",
        "entity_type",
        "entity_id",
        "source_component",
        "correlation_id",
    ),
)
def test_event_rejects_blank_required_identity(field_name):
    with pytest.raises(ValueError):
        make_event(**{field_name: "   "})


def test_event_rejects_unknown_schema_version():
    with pytest.raises(ValueError):
        make_event(schema_version="2")


def test_event_payload_is_deeply_immutable_and_copied():
    source = {
        "context": {
            "labels": ["local"],
        },
    }

    event = make_event(payload=source)
    source["context"]["labels"].append("changed")

    assert event.payload["context"]["labels"] == ("local",)

    with pytest.raises(TypeError):
        event.payload["new"] = "value"

    with pytest.raises(TypeError):
        event.payload["context"]["new"] = "value"


def test_event_rejects_secret_bearing_payload_keys():
    with pytest.raises(ValueError):
        make_event(
            payload={
                "context": {
                    "api_key": "must-not-enter-event",
                },
            },
        )


def test_event_rejects_non_json_payload_values():
    with pytest.raises(TypeError, match="payload"):
        make_event(payload={"unsafe": object()})


def test_audit_record_is_separate_from_work_event():
    audit = make_audit()

    assert not isinstance(audit, events.WorkEvent)
    assert audit.audit_id == "audit-1"
    assert audit.event_id == "event-1"
    assert audit.reason_code == "owner_request"


def test_audit_policy_and_approval_fields_are_reserved_optional():
    audit = make_audit()

    assert audit.policy_version is None
    assert audit.approval_id is None
    assert audit.on_behalf_of is None


def test_audit_rejects_blank_required_fields():
    with pytest.raises(ValueError):
        make_audit(action="   ")


def test_append_result_contract_is_stable():
    assert tuple(item.value for item in events.AppendResult) == (
        "appended",
        "idempotent_replay",
        "identity_conflict",
        "schema_rejected",
        "write_failed",
        "integrity_failed",
    )


def test_new_audit_id_is_traceable():
    assert events.new_audit_id().startswith("audit-")
