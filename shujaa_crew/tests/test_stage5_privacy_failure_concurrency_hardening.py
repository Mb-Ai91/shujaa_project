from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import inspect

import pytest

import core.work.event_store as store_module
from core.work.events import AppendResult, AuditRecord, WorkEvent


UTC_TIME = datetime(
    2026,
    8,
    23,
    12,
    0,
    tzinfo=timezone.utc,
)


def make_event(**overrides):
    values = {
        "event_id": "event-hardening-1",
        "event_type": "execution.started",
        "entity_type": "execution",
        "entity_id": "exec-hardening-1",
        "source_component": "core.manager",
        "correlation_id": "work-hardening-1",
        "occurred_at": UTC_TIME,
        "recorded_at": UTC_TIME,
        "payload": {"reason_code": "accepted"},
    }
    values.update(overrides)
    return WorkEvent(**values)


def make_audit(**overrides):
    values = {
        "audit_id": "audit-hardening-1",
        "action": "execution.start",
        "actor_type": "system",
        "actor_id": "shujaa_manager",
        "resource_type": "execution",
        "resource_id": "exec-hardening-1",
        "outcome": "accepted",
        "reason_code": "execution_started",
        "recorded_at": UTC_TIME,
        "operation_id": "operation-hardening-1",
    }
    values.update(overrides)
    return AuditRecord(**values)


def test_event_rejects_extended_sensitive_key_variants():
    sensitive_keys = (
        "access_token_value",
        "client_credentials",
        "private_key_pem",
        "password_plaintext",
        "authentication_cookie_value",
    )

    for key in sensitive_keys:
        with pytest.raises(ValueError):
            make_event(
                payload={
                    "context": {
                        key: "raw-sensitive-value",
                    },
                },
            )


def test_event_allows_explicit_safe_reference_keys():
    event = make_event(
        payload={
            "secret_reference": "vault-reference-1",
            "credential_reference": "credential-reference-1",
            "token_reference": "token-reference-1",
        },
    )

    assert event.payload == {
        "secret_reference": "vault-reference-1",
        "credential_reference": "credential-reference-1",
        "token_reference": "token-reference-1",
    }


def test_store_protocols_expose_integrity_verification_contract():
    for protocol in (
        store_module.EventStoreProtocol,
        store_module.AuditStoreProtocol,
    ):
        method = getattr(protocol, "verify_integrity")
        assert list(inspect.signature(method).parameters) == [
            "self",
        ]


def test_healthy_event_and_audit_stores_verify_integrity():
    cases = (
        (
            store_module.InMemoryEventStore(),
            make_event,
            "event",
        ),
        (
            store_module.InMemoryAuditStore(),
            make_audit,
            "audit",
        ),
    )

    for store, factory, prefix in cases:
        for number in range(1, 3):
            overrides = {
                f"{prefix}_id": f"{prefix}-hardening-{number}",
            }
            receipt = store.append(factory(**overrides))
            assert receipt.result is AppendResult.APPENDED

        verification = store.verify_integrity()
        assert verification.result is (
            store_module.IntegrityResult.VALID
        )
        assert verification.checked_entries == 2
        assert verification.invalid_sequence is None
        assert verification.error_code is None


def test_integrity_verification_detects_entry_tampering():
    store = store_module.InMemoryEventStore()
    store.append(make_event())

    original = store._entries[0]
    store._entries[0] = replace(
        original,
        integrity_hash="0" * 64,
    )

    verification = store.verify_integrity()

    assert verification.result is (
        store_module.IntegrityResult.CORRUPTED
    )
    assert verification.checked_entries == 1
    assert verification.invalid_sequence == 1
    assert verification.error_code == (
        "integrity_hash_mismatch"
    )


def test_integrity_verification_detects_canonical_index_corruption():
    store = store_module.InMemoryAuditStore()
    audit = make_audit()
    store.append(audit)
    store._canonical_by_id[audit.audit_id] = b"{}"

    verification = store.verify_integrity()

    assert verification.result is (
        store_module.IntegrityResult.CORRUPTED
    )
    assert verification.checked_entries == 1
    assert verification.invalid_sequence == 1
    assert verification.error_code == (
        "canonical_index_mismatch"
    )


def test_append_fails_closed_when_existing_chain_is_corrupted():
    store = store_module.InMemoryEventStore()
    store.append(make_event())
    store._entries[0] = replace(
        store._entries[0],
        integrity_hash="0" * 64,
    )

    receipt = store.append(
        make_event(
            event_id="event-hardening-2",
            entity_id="exec-hardening-2",
        ),
    )

    assert receipt.result is AppendResult.INTEGRITY_FAILED
    assert receipt.record_id == "event-hardening-2"
    assert receipt.local_sequence is None
    assert receipt.integrity_hash is None
    assert receipt.error_code == "integrity_hash_mismatch"
    assert len(store._entries) == 1


def test_concurrent_identical_audits_are_replay_stable():
    store = store_module.InMemoryAuditStore()

    audits = [
        make_audit(
            recorded_at=(
                UTC_TIME + timedelta(microseconds=number)
            ),
        )
        for number in range(20)
    ]

    with ThreadPoolExecutor(max_workers=8) as executor:
        receipts = list(
            executor.map(
                store.append_replay_stable,
                audits,
            ),
        )

    assert sum(
        receipt.result is AppendResult.APPENDED
        for receipt in receipts
    ) == 1
    assert sum(
        receipt.result is AppendResult.IDEMPOTENT_REPLAY
        for receipt in receipts
    ) == 19
    assert len(store.list()) == 1


def test_concurrent_conflicting_audits_preserve_one_winner():
    store = store_module.InMemoryAuditStore()

    audits = [
        make_audit(
            outcome=(
                "accepted"
                if number % 2 == 0
                else "rejected"
            ),
            recorded_at=(
                UTC_TIME + timedelta(microseconds=number)
            ),
        )
        for number in range(20)
    ]

    with ThreadPoolExecutor(max_workers=8) as executor:
        receipts = list(
            executor.map(
                store.append_replay_stable,
                audits,
            ),
        )

    assert sum(
        receipt.result is AppendResult.APPENDED
        for receipt in receipts
    ) == 1
    assert sum(
        receipt.result is AppendResult.IDEMPOTENT_REPLAY
        for receipt in receipts
    ) == 9
    assert sum(
        receipt.result is AppendResult.IDENTITY_CONFLICT
        for receipt in receipts
    ) == 10
    assert len(store.list()) == 1


def test_audit_write_failure_consumes_no_sequence():
    def failing_hasher(data):
        raise OSError("simulated audit write failure")

    store = store_module.InMemoryAuditStore(
        integrity_hasher=failing_hasher,
    )

    receipt = store.append(make_audit())

    assert receipt.result is AppendResult.WRITE_FAILED
    assert receipt.record_id == "audit-hardening-1"
    assert receipt.local_sequence is None
    assert receipt.integrity_hash is None
    assert receipt.error_code == "OSError"
    assert store.list() == ()
