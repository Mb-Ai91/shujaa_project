from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass, fields, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
from threading import Lock
from typing import Any, Generic, Protocol, TypeVar

from core.work.events import (
    AppendResult,
    AuditRecord,
    WorkEvent,
)


RecordT = TypeVar(
    "RecordT",
    WorkEvent,
    AuditRecord,
)

IntegrityHasher = Callable[[bytes], str]


@dataclass(frozen=True)
class StoredEntry(Generic[RecordT]):
    """Immutable entry in a local append-only store."""

    record: RecordT
    local_sequence: int
    integrity_hash: str
    previous_integrity_hash: str | None


@dataclass(frozen=True)
class AppendReceipt:
    """Structured result returned by a local append attempt."""

    result: AppendResult
    record_id: str | None
    local_sequence: int | None = None
    integrity_hash: str | None = None
    error_code: str | None = None


class EventStoreProtocol(Protocol):
    """Minimal replaceable contract for WorkEvent persistence."""

    def append(
        self,
        record: WorkEvent,
    ) -> AppendReceipt:
        ...

    def get(
        self,
        record_id: str,
    ) -> StoredEntry[WorkEvent] | None:
        ...

    def list(
        self,
        after_sequence: int = 0,
        limit: int | None = None,
    ) -> tuple[StoredEntry[WorkEvent], ...]:
        ...


class AuditStoreProtocol(Protocol):
    """Minimal replaceable contract for AuditRecord persistence."""

    def append(
        self,
        record: AuditRecord,
    ) -> AppendReceipt:
        ...

    def get(
        self,
        record_id: str,
    ) -> StoredEntry[AuditRecord] | None:
        ...

    def list(
        self,
        after_sequence: int = 0,
        limit: int | None = None,
    ) -> tuple[StoredEntry[AuditRecord], ...]:
        ...


def _default_integrity_hasher(payload: bytes) -> str:
    return sha256(payload).hexdigest()


def _canonical_value(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {
            item.name: _canonical_value(
                getattr(value, item.name)
            )
            for item in fields(value)
        }

    if isinstance(value, datetime):
        normalized = value.astimezone(timezone.utc)
        return normalized.isoformat().replace(
            "+00:00",
            "Z",
        )

    if isinstance(value, Enum):
        return _canonical_value(value.value)

    if isinstance(value, Mapping):
        return {
            str(key): _canonical_value(value[key])
            for key in sorted(
                value,
                key=lambda item: str(item),
            )
        }

    if isinstance(value, (tuple, list)):
        return [
            _canonical_value(item)
            for item in value
        ]

    if value is None or isinstance(
        value,
        (str, int, float, bool),
    ):
        return value

    raise TypeError(
        "Value is not canonically serializable: "
        f"{type(value).__name__}"
    )


def _canonical_bytes(record: object) -> bytes:
    return json.dumps(
        _canonical_value(record),
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


class _InMemoryAppendStore(Generic[RecordT]):
    """Thread-safe local/mock append foundation.

    Integrity hashes detect local inconsistency. They are not a claim
    of production-grade tamper resistance or distributed ordering.
    """

    def __init__(
        self,
        *,
        record_type: type[RecordT],
        identity_attribute: str,
        integrity_hasher: IntegrityHasher | None = None,
    ) -> None:
        self._record_type = record_type
        self._identity_attribute = identity_attribute
        self._integrity_hasher = (
            integrity_hasher
            or _default_integrity_hasher
        )
        self._entries: list[StoredEntry[RecordT]] = []
        self._entries_by_id: dict[
            str,
            StoredEntry[RecordT],
        ] = {}
        self._canonical_by_id: dict[str, bytes] = {}
        self._lock = Lock()

    def append(
        self,
        record: RecordT,
    ) -> AppendReceipt:
        if not isinstance(record, self._record_type):
            return AppendReceipt(
                result=AppendResult.SCHEMA_REJECTED,
                record_id=None,
                error_code="invalid_record_type",
            )

        record_id = getattr(
            record,
            self._identity_attribute,
        )

        try:
            canonical_record = _canonical_bytes(record)
        except Exception as error:
            return AppendReceipt(
                result=AppendResult.SCHEMA_REJECTED,
                record_id=record_id,
                error_code=type(error).__name__,
            )

        with self._lock:
            existing = self._entries_by_id.get(record_id)

            if existing is not None:
                if (
                    self._canonical_by_id[record_id]
                    == canonical_record
                ):
                    return AppendReceipt(
                        result=AppendResult.IDEMPOTENT_REPLAY,
                        record_id=record_id,
                        local_sequence=(
                            existing.local_sequence
                        ),
                        integrity_hash=(
                            existing.integrity_hash
                        ),
                    )

                return AppendReceipt(
                    result=AppendResult.IDENTITY_CONFLICT,
                    record_id=record_id,
                )

            local_sequence = len(self._entries) + 1
            previous_hash = (
                self._entries[-1].integrity_hash
                if self._entries
                else None
            )

            integrity_material = json.dumps(
                {
                    "local_sequence": local_sequence,
                    "previous_integrity_hash": (
                        previous_hash
                    ),
                    "record": json.loads(
                        canonical_record.decode("utf-8")
                    ),
                },
                ensure_ascii=False,
                allow_nan=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")

            try:
                integrity_hash = (
                    self._integrity_hasher(
                        integrity_material
                    )
                )

                if not isinstance(
                    integrity_hash,
                    str,
                ) or not integrity_hash:
                    raise ValueError(
                        "integrity_hasher returned "
                        "an invalid digest"
                    )
            except Exception as error:
                return AppendReceipt(
                    result=AppendResult.WRITE_FAILED,
                    record_id=record_id,
                    error_code=type(error).__name__,
                )

            entry = StoredEntry(
                record=record,
                local_sequence=local_sequence,
                integrity_hash=integrity_hash,
                previous_integrity_hash=previous_hash,
            )

            self._entries.append(entry)
            self._entries_by_id[record_id] = entry
            self._canonical_by_id[
                record_id
            ] = canonical_record

            return AppendReceipt(
                result=AppendResult.APPENDED,
                record_id=record_id,
                local_sequence=local_sequence,
                integrity_hash=integrity_hash,
            )

    def get(
        self,
        record_id: str,
    ) -> StoredEntry[RecordT] | None:
        with self._lock:
            return self._entries_by_id.get(record_id)

    def list(
        self,
        after_sequence: int = 0,
        limit: int | None = None,
    ) -> tuple[StoredEntry[RecordT], ...]:
        if after_sequence < 0:
            raise ValueError(
                "after_sequence must be non-negative"
            )

        if limit is not None and limit <= 0:
            raise ValueError(
                "limit must be positive"
            )

        with self._lock:
            entries = tuple(
                entry
                for entry in self._entries
                if (
                    entry.local_sequence
                    > after_sequence
                )
            )

            if limit is not None:
                entries = entries[:limit]

            return entries


class InMemoryEventStore(
    _InMemoryAppendStore[WorkEvent]
):
    """Replaceable local/mock WorkEvent append store."""

    def __init__(
        self,
        *,
        integrity_hasher: IntegrityHasher | None = None,
    ) -> None:
        super().__init__(
            record_type=WorkEvent,
            identity_attribute="event_id",
            integrity_hasher=integrity_hasher,
        )


class InMemoryAuditStore(
    _InMemoryAppendStore[AuditRecord]
):
    """Replaceable local/mock AuditRecord append store."""

    def __init__(
        self,
        *,
        integrity_hasher: IntegrityHasher | None = None,
    ) -> None:
        super().__init__(
            record_type=AuditRecord,
            identity_attribute="audit_id",
            integrity_hasher=integrity_hasher,
        )
