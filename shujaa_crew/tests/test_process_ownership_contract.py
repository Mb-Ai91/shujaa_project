from concurrent.futures import ThreadPoolExecutor
from importlib import import_module

import pytest

from core.runtime.process_registry import ProcessRegistry


def _contract():
    return import_module(
        "core.runtime.process_registry_contract"
    )


def _ownership(
    *,
    task_id="task-1",
    execution_id="exec-1",
    pid=1001,
    pgid=2001,
    process_start_time_ticks=3001,
):
    contract = _contract()

    return contract.ProcessOwnership(
        task_id=task_id,
        execution_id=execution_id,
        pid=pid,
        pgid=pgid,
        process_start_time_ticks=process_start_time_ticks,
    )


def test_registry_implements_process_registry_protocol(tmp_path):
    contract = _contract()
    registry = ProcessRegistry(tmp_path / "processes.json")

    assert isinstance(
        registry,
        contract.ProcessRegistryProtocol,
    )


def test_register_records_new_typed_owner(tmp_path):
    contract = _contract()
    registry = ProcessRegistry(tmp_path / "processes.json")
    owner = _ownership()

    result = registry.register(owner)

    assert (
        result.disposition
        == contract.RegistrationDisposition.REGISTERED
    )
    assert result.ownership == owner
    assert registry.get(owner.task_id) == owner
    assert registry.all() == {owner.task_id: owner}


def test_register_same_owner_is_idempotent(tmp_path):
    contract = _contract()
    registry = ProcessRegistry(tmp_path / "processes.json")
    owner = _ownership()

    first = registry.register(owner)
    replay = registry.register(owner)

    assert (
        first.disposition
        == contract.RegistrationDisposition.REGISTERED
    )
    assert (
        replay.disposition
        == contract.RegistrationDisposition.IDEMPOTENT_REPLAY
    )
    assert replay.ownership == owner
    assert registry.get(owner.task_id) == owner


def test_register_different_owner_preserves_existing_owner(tmp_path):
    contract = _contract()
    registry = ProcessRegistry(tmp_path / "processes.json")
    first_owner = _ownership()
    competing_owner = _ownership(
        execution_id="exec-2",
        pid=1002,
        pgid=2002,
        process_start_time_ticks=3002,
    )

    registry.register(first_owner)
    conflict = registry.register(competing_owner)

    assert (
        conflict.disposition
        == contract.RegistrationDisposition.OWNER_CONFLICT
    )
    assert conflict.ownership == first_owner
    assert registry.get(first_owner.task_id) == first_owner


def test_release_matching_owner_removes_registration(tmp_path):
    contract = _contract()
    registry = ProcessRegistry(tmp_path / "processes.json")
    owner = _ownership()
    registry.register(owner)

    result = registry.release(
        owner.task_id,
        expected_execution_id=owner.execution_id,
    )

    assert (
        result.disposition
        == contract.ReleaseDisposition.RELEASED
    )
    assert result.ownership == owner
    assert registry.get(owner.task_id) is None


def test_release_missing_owner_is_idempotent(tmp_path):
    contract = _contract()
    registry = ProcessRegistry(tmp_path / "processes.json")

    result = registry.release(
        "missing-task",
        expected_execution_id="exec-missing",
    )

    assert (
        result.disposition
        == contract.ReleaseDisposition.NOT_FOUND
    )
    assert result.ownership is None


def test_release_wrong_execution_preserves_owner(tmp_path):
    contract = _contract()
    registry = ProcessRegistry(tmp_path / "processes.json")
    owner = _ownership()
    registry.register(owner)

    result = registry.release(
        owner.task_id,
        expected_execution_id="exec-stale",
    )

    assert (
        result.disposition
        == contract.ReleaseDisposition.OWNER_MISMATCH
    )
    assert result.ownership == owner
    assert registry.get(owner.task_id) == owner


def test_stale_release_cannot_remove_newer_owner(tmp_path):
    contract = _contract()
    registry = ProcessRegistry(tmp_path / "processes.json")
    old_owner = _ownership()
    new_owner = _ownership(
        execution_id="exec-2",
        pid=1002,
        pgid=2002,
        process_start_time_ticks=3002,
    )

    registry.register(old_owner)
    registry.release(
        old_owner.task_id,
        expected_execution_id=old_owner.execution_id,
    )
    registry.register(new_owner)

    stale_release = registry.release(
        old_owner.task_id,
        expected_execution_id=old_owner.execution_id,
    )

    assert (
        stale_release.disposition
        == contract.ReleaseDisposition.OWNER_MISMATCH
    )
    assert stale_release.ownership == new_owner
    assert registry.get(old_owner.task_id) == new_owner


def test_corrupt_registry_is_not_treated_as_empty(tmp_path):
    contract = _contract()
    registry_path = tmp_path / "processes.json"
    corrupt_payload = "{not-valid-json"
    registry_path.write_text(
        corrupt_payload,
        encoding="utf-8",
    )
    registry = ProcessRegistry(registry_path)

    with pytest.raises(
        contract.ProcessRegistryCorruptionError
    ):
        registry.all()

    assert (
        registry_path.read_text(encoding="utf-8")
        == corrupt_payload
    )


def test_concurrent_same_owner_registration_is_idempotent(
    tmp_path,
):
    contract = _contract()
    registry_path = tmp_path / "processes.json"
    owner = _ownership()

    def register_owner(_):
        registry = ProcessRegistry(registry_path)
        return registry.register(owner).disposition

    with ThreadPoolExecutor(max_workers=8) as executor:
        dispositions = list(
            executor.map(register_owner, range(20))
        )

    assert dispositions.count(
        contract.RegistrationDisposition.REGISTERED
    ) == 1
    assert dispositions.count(
        contract.RegistrationDisposition.IDEMPOTENT_REPLAY
    ) == 19
    assert ProcessRegistry(registry_path).get(
        owner.task_id
    ) == owner

@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("task_id", ""),
        ("execution_id", ""),
        ("pid", 0),
        ("pid", -1),
        ("pgid", 0),
        ("pgid", -1),
        ("process_start_time_ticks", 0),
    ],
)
def test_process_ownership_rejects_invalid_identity(
    field,
    value,
):
    contract = _contract()
    values = {
        "task_id": "task-valid",
        "execution_id": "exec-valid",
        "pid": 6101,
        "pgid": 6201,
        "process_start_time_ticks": 6301,
    }
    values[field] = value

    with pytest.raises(ValueError):
        contract.ProcessOwnership(**values)


def test_registry_rejects_persisted_nonpositive_identity(
    tmp_path,
):
    contract = _contract()
    registry_path = tmp_path / "processes.json"
    registry_path.write_text(
        """{
  "task-invalid": {
    "execution_id": "exec-invalid",
    "pid": 6101,
    "pgid": 0,
    "process_start_time_ticks": 6301
  }
}""",
        encoding="utf-8",
    )
    registry = ProcessRegistry(registry_path)

    with pytest.raises(
        contract.ProcessRegistryCorruptionError
    ):
        registry.all()


def test_registry_has_no_unconditional_clear_capability(
    tmp_path,
):
    registry = ProcessRegistry(tmp_path / "processes.json")

    assert not hasattr(registry, "clear")




def test_registry_rejects_legacy_owner_without_execution_id(
    tmp_path,
):
    contract = _contract()
    registry_path = tmp_path / "processes.json"
    registry_path.write_text(
        """{
  "task-legacy": {
    "pid": 7101,
    "pgid": 7201
  }
}""",
        encoding="utf-8",
    )
    registry = ProcessRegistry(registry_path)

    with pytest.raises(
        contract.ProcessRegistryCorruptionError
    ):
        registry.all()
