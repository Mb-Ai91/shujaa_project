from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
import importlib
import inspect

import pytest

from core.work.events import (
    AppendResult,
    AuditRecord,
    WorkEvent,
)


UTC_TIME = datetime(
    2026,
    8,
    17,
    12,
    0,
    tzinfo=timezone.utc,
)


def store_api():
    return importlib.import_module(
        "core.work.event_store"
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
        "payload": {
            "reason_code": "accepted",
        },
    }
    values.update(overrides)
    return WorkEvent(**values)


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
    }
    values.update(overrides)
    return AuditRecord(**values)


def test_store_protocols_declare_minimal_surface():
    api = store_api()

    for protocol in (
        api.EventStoreProtocol,
        api.AuditStoreProtocol,
    ):
        assert list(
            inspect.signature(
                protocol.append
            ).parameters
        ) == ["self", "record"]

        assert list(
            inspect.signature(
                protocol.get
            ).parameters
        ) == ["self", "record_id"]

        assert list(
            inspect.signature(
                protocol.list
            ).parameters
        ) == [
            "self",
            "after_sequence",
            "limit",
        ]


def test_event_store_appends_with_local_integrity_metadata():
    api = store_api()
    store = api.InMemoryEventStore()
    event = make_event()

    receipt = store.append(event)
    entry = store.get(event.event_id)

    assert receipt.result is AppendResult.APPENDED
    assert receipt.record_id == event.event_id
    assert receipt.local_sequence == 1
    assert len(receipt.integrity_hash) == 64
    assert receipt.error_code is None

    assert entry.record == event
    assert entry.local_sequence == 1
    assert entry.previous_integrity_hash is None
    assert entry.integrity_hash == (
        receipt.integrity_hash
    )


def test_audit_store_appends_audit_record():
    api = store_api()
    store = api.InMemoryAuditStore()
    audit = make_audit()

    receipt = store.append(audit)
    entry = store.get(audit.audit_id)

    assert receipt.result is AppendResult.APPENDED
    assert receipt.record_id == audit.audit_id
    assert receipt.local_sequence == 1
    assert entry.record == audit


def test_event_and_audit_replay_is_idempotent():
    api = store_api()

    cases = (
        (
            api.InMemoryEventStore(),
            make_event(),
            "event-1",
        ),
        (
            api.InMemoryAuditStore(),
            make_audit(),
            "audit-1",
        ),
    )

    for store, record, record_id in cases:
        first = store.append(record)
        replay = store.append(record)

        assert first.result is AppendResult.APPENDED
        assert (
            replay.result
            is AppendResult.IDEMPOTENT_REPLAY
        )
        assert replay.record_id == record_id
        assert replay.local_sequence == 1
        assert replay.integrity_hash == (
            first.integrity_hash
        )
        assert len(store.list()) == 1


def test_identity_conflict_preserves_original_record():
    api = store_api()

    event_store = api.InMemoryEventStore()
    first_event = make_event()
    conflicting_event = make_event(
        event_type="execution.failed",
    )

    event_store.append(first_event)
    event_conflict = event_store.append(
        conflicting_event
    )

    assert (
        event_conflict.result
        is AppendResult.IDENTITY_CONFLICT
    )
    assert event_store.get("event-1").record == (
        first_event
    )

    audit_store = api.InMemoryAuditStore()
    first_audit = make_audit()
    conflicting_audit = make_audit(
        outcome="denied",
    )

    audit_store.append(first_audit)
    audit_conflict = audit_store.append(
        conflicting_audit
    )

    assert (
        audit_conflict.result
        is AppendResult.IDENTITY_CONFLICT
    )
    assert audit_store.get("audit-1").record == (
        first_audit
    )


def test_local_sequence_and_minimal_query_are_ordered():
    api = store_api()
    store = api.InMemoryEventStore()

    for number in range(1, 4):
        receipt = store.append(
            make_event(
                event_id=f"event-{number}",
                entity_id=f"exec-{number}",
            )
        )
        assert receipt.local_sequence == number

    entries = store.list(
        after_sequence=1,
        limit=1,
    )

    assert isinstance(entries, tuple)
    assert len(entries) == 1
    assert entries[0].local_sequence == 2
    assert entries[0].record.event_id == "event-2"


def test_get_unknown_identity_returns_none():
    api = store_api()

    assert (
        api.InMemoryEventStore().get("missing")
        is None
    )
    assert (
        api.InMemoryAuditStore().get("missing")
        is None
    )


def test_wrong_record_type_is_schema_rejected():
    api = store_api()
    store = api.InMemoryEventStore()

    receipt = store.append(object())

    assert (
        receipt.result
        is AppendResult.SCHEMA_REJECTED
    )
    assert receipt.record_id is None
    assert receipt.local_sequence is None
    assert receipt.integrity_hash is None
    assert receipt.error_code == "invalid_record_type"
    assert store.list() == ()


def test_write_failure_is_structured_and_consumes_no_sequence():
    api = store_api()

    def failing_hasher(data):
        raise OSError("simulated write failure")

    store = api.InMemoryEventStore(
        integrity_hasher=failing_hasher,
    )

    receipt = store.append(make_event())

    assert receipt.result is AppendResult.WRITE_FAILED
    assert receipt.record_id == "event-1"
    assert receipt.local_sequence is None
    assert receipt.integrity_hash is None
    assert receipt.error_code == "OSError"
    assert store.list() == ()


def test_integrity_chain_links_local_entries():
    api = store_api()
    store = api.InMemoryEventStore()

    store.append(
        make_event(
            event_id="event-1",
            entity_id="exec-1",
        )
    )
    store.append(
        make_event(
            event_id="event-2",
            entity_id="exec-2",
        )
    )

    first, second = store.list()

    assert first.previous_integrity_hash is None
    assert second.previous_integrity_hash == (
        first.integrity_hash
    )
    assert second.integrity_hash != (
        first.integrity_hash
    )


def test_event_and_audit_sequences_are_independent():
    api = store_api()
    event_store = api.InMemoryEventStore()
    audit_store = api.InMemoryAuditStore()

    event_receipt = event_store.append(
        make_event()
    )
    audit_receipt = audit_store.append(
        make_audit()
    )

    assert event_receipt.local_sequence == 1
    assert audit_receipt.local_sequence == 1


def test_stored_entries_are_immutable():
    api = store_api()
    store = api.InMemoryEventStore()

    store.append(make_event())
    entry = store.get("event-1")

    with pytest.raises(FrozenInstanceError):
        entry.local_sequence = 99


def test_concurrent_appends_receive_unique_sequences():
    api = store_api()
    store = api.InMemoryEventStore()

    events = [
        make_event(
            event_id=f"event-{number}",
            entity_id=f"exec-{number}",
        )
        for number in range(20)
    ]

    with ThreadPoolExecutor(
        max_workers=8
    ) as executor:
        receipts = list(
            executor.map(store.append, events)
        )

    assert all(
        receipt.result is AppendResult.APPENDED
        for receipt in receipts
    )

    assert sorted(
        receipt.local_sequence
        for receipt in receipts
    ) == list(range(1, 21))

    assert [
        entry.local_sequence
        for entry in store.list()
    ] == list(range(1, 21))
