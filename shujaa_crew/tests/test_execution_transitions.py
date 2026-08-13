from threading import Barrier, Lock, Thread

import pytest

from core.work.execution_registry import InMemoryExecutionRegistry
from core.work.models import Execution, ExecutionStatus


def make_registry():
    registry = InMemoryExecutionRegistry()
    execution = Execution(
        execution_id="exec-transition-test",
        work_id="work-transition-test",
        task_id="task-transition-test",
    )
    registry.create(execution)
    return registry, execution.execution_id


def commit_authorized_transition(
    registry,
    execution_id,
    target_status,
    *,
    expected_version,
    operation_id,
):
    """Commit a transition already authorized by Manager/Lifecycle Authority."""
    return registry.transition(
        execution_id,
        target_status=target_status,
        expected_version=expected_version,
        operation_id=operation_id,
        source="manager_lifecycle_authority",
    )


def test_transition_applies_with_expected_version():
    registry, execution_id = make_registry()

    result = commit_authorized_transition(
        registry,
        execution_id,
        ExecutionStatus.RUNNING,
        expected_version=0,
        operation_id="start-1",
    )

    assert result.applied is True
    assert result.disposition.value == "applied"
    assert result.execution.status == ExecutionStatus.RUNNING
    assert result.execution.state_version == 1


def test_stale_expected_version_is_rejected_without_mutation():
    registry, execution_id = make_registry()

    commit_authorized_transition(
        registry,
        execution_id,
        ExecutionStatus.RUNNING,
        expected_version=0,
        operation_id="start-1",
    )

    stale = commit_authorized_transition(
        registry,
        execution_id,
        ExecutionStatus.FAILED,
        expected_version=0,
        operation_id="failure-1",
    )

    stored = registry.get(execution_id)

    assert stale.applied is False
    assert stale.disposition.value == "stale_version"
    assert stored is not None
    assert stored.status == ExecutionStatus.RUNNING
    assert stored.state_version == 1


def test_same_terminal_operation_is_idempotent():
    registry, execution_id = make_registry()

    commit_authorized_transition(
        registry,
        execution_id,
        ExecutionStatus.RUNNING,
        expected_version=0,
        operation_id="start-1",
    )

    accepted = commit_authorized_transition(
        registry,
        execution_id,
        ExecutionStatus.COMPLETED,
        expected_version=1,
        operation_id="completion-1",
    )

    replay = commit_authorized_transition(
        registry,
        execution_id,
        ExecutionStatus.COMPLETED,
        expected_version=1,
        operation_id="completion-1",
    )

    assert accepted.execution.state_version == 2
    assert replay.applied is False
    assert replay.disposition.value == "idempotent_replay"
    assert replay.execution.status == ExecutionStatus.COMPLETED
    assert replay.execution.state_version == 2


def test_different_terminal_attempt_is_structured_and_cannot_overwrite():
    registry, execution_id = make_registry()

    commit_authorized_transition(
        registry,
        execution_id,
        ExecutionStatus.RUNNING,
        expected_version=0,
        operation_id="start-1",
    )

    commit_authorized_transition(
        registry,
        execution_id,
        ExecutionStatus.COMPLETED,
        expected_version=1,
        operation_id="completion-1",
    )

    losing = commit_authorized_transition(
        registry,
        execution_id,
        ExecutionStatus.FAILED,
        expected_version=2,
        operation_id="failure-1",
    )

    stored = registry.get(execution_id)

    assert losing.applied is False
    assert losing.disposition.value == "conflicting_terminal_attempt"
    assert losing.observation is not None
    assert losing.observation.operation_id == "failure-1"
    assert losing.observation.attempted_status == ExecutionStatus.FAILED
    assert losing.observation.rejected_at_version == 2
    assert stored is not None
    assert stored.status == ExecutionStatus.COMPLETED
    assert stored.state_version == 2


def test_manager_lifecycle_authority_applies_valid_transition():
    from core.manager.service import ShujaaManager

    class UnusedRunner:
        def start(self, command):
            raise AssertionError("Runner must not be called.")

    manager = ShujaaManager(crew_runner=UnusedRunner())
    execution = Execution(
        execution_id="exec-manager-valid",
        work_id="work-manager-valid",
        task_id="task-manager-valid",
    )
    manager.execution_registry.create(execution)

    result = manager._transition_execution(
        execution.execution_id,
        target_status=ExecutionStatus.RUNNING,
        operation_id="start-manager-1",
    )

    assert result.applied is True
    assert result.execution.status == ExecutionStatus.RUNNING
    assert result.execution.state_version == 1


def test_manager_lifecycle_authority_rejects_invalid_transition():
    import pytest

    from core.manager.service import ShujaaManager

    class UnusedRunner:
        def start(self, command):
            raise AssertionError("Runner must not be called.")

    manager = ShujaaManager(crew_runner=UnusedRunner())
    execution = Execution(
        execution_id="exec-manager-invalid",
        work_id="work-manager-invalid",
        task_id="task-manager-invalid",
    )
    manager.execution_registry.create(execution)

    with pytest.raises(
        ValueError,
        match="Invalid execution transition",
    ):
        manager._transition_execution(
            execution.execution_id,
            target_status=ExecutionStatus.COMPLETED,
            operation_id="completion-manager-1",
        )

    stored = manager.execution_registry.get(
        execution.execution_id
    )

    assert stored is not None
    assert stored.status == ExecutionStatus.QUEUED
    assert stored.state_version == 0


def make_manager_transition_fixture(
    execution_id,
):
    from core.manager.service import ShujaaManager

    class UnusedRunner:
        def start(self, command):
            raise AssertionError("Runner must not be called.")

    manager = ShujaaManager(crew_runner=UnusedRunner())
    execution = Execution(
        execution_id=execution_id,
        work_id=f"work-{execution_id}",
        task_id=f"task-{execution_id}",
    )
    manager.execution_registry.create(execution)
    return manager, execution


@pytest.mark.parametrize(
    "target_status",
    (
        ExecutionStatus.COMPLETED,
        ExecutionStatus.FAILED,
        ExecutionStatus.CANCELLED,
        ExecutionStatus.TIMED_OUT,
    ),
)
def test_manager_lifecycle_authority_applies_terminal_transition(
    target_status,
):
    manager, execution = make_manager_transition_fixture(
        f"exec-manager-{target_status.value}"
    )

    started = manager._transition_execution(
        execution.execution_id,
        target_status=ExecutionStatus.RUNNING,
        operation_id="start-manager-1",
    )

    operation_id = f"{target_status.value}-manager-1"

    terminal = manager._transition_execution(
        execution.execution_id,
        target_status=target_status,
        operation_id=operation_id,
    )

    assert started.applied is True
    assert terminal.applied is True
    assert terminal.disposition.value == "applied"
    assert terminal.execution.status == target_status
    assert terminal.execution.state_version == 2
    assert (
        terminal.execution.terminal_operation_id
        == operation_id
    )


def test_manager_lifecycle_authority_allows_failure_before_running():
    manager, execution = make_manager_transition_fixture(
        "exec-manager-pre-start-failure"
    )

    failed = manager._transition_execution(
        execution.execution_id,
        target_status=ExecutionStatus.FAILED,
        operation_id="pre-start-failure-manager-1",
    )

    assert failed.applied is True
    assert failed.disposition.value == "applied"
    assert failed.execution.status == ExecutionStatus.FAILED
    assert failed.execution.state_version == 1
    assert (
        failed.execution.terminal_operation_id
        == "pre-start-failure-manager-1"
    )


def test_manager_lifecycle_authority_returns_idempotent_replay():
    manager, execution = make_manager_transition_fixture(
        "exec-manager-terminal-replay"
    )

    manager._transition_execution(
        execution.execution_id,
        target_status=ExecutionStatus.RUNNING,
        operation_id="start-manager-replay-1",
    )

    accepted = manager._transition_execution(
        execution.execution_id,
        target_status=ExecutionStatus.COMPLETED,
        operation_id="completion-manager-replay-1",
    )

    replay = manager._transition_execution(
        execution.execution_id,
        target_status=ExecutionStatus.COMPLETED,
        operation_id="completion-manager-replay-1",
    )

    assert accepted.applied is True
    assert replay.applied is False
    assert replay.disposition.value == "idempotent_replay"
    assert replay.execution.status == ExecutionStatus.COMPLETED
    assert replay.execution.state_version == 2


def test_manager_lifecycle_authority_returns_terminal_conflict():
    manager, execution = make_manager_transition_fixture(
        "exec-manager-terminal-conflict"
    )

    manager._transition_execution(
        execution.execution_id,
        target_status=ExecutionStatus.RUNNING,
        operation_id="start-manager-conflict-1",
    )

    manager._transition_execution(
        execution.execution_id,
        target_status=ExecutionStatus.COMPLETED,
        operation_id="completion-manager-conflict-1",
    )

    losing = manager._transition_execution(
        execution.execution_id,
        target_status=ExecutionStatus.FAILED,
        operation_id="failure-manager-conflict-1",
    )

    assert losing.applied is False
    assert (
        losing.disposition.value
        == "conflicting_terminal_attempt"
    )
    assert losing.execution.status == ExecutionStatus.COMPLETED
    assert losing.execution.state_version == 2
    assert losing.observation is not None
    assert (
        losing.observation.operation_id
        == "failure-manager-conflict-1"
    )
    assert (
        losing.observation.attempted_status
        == ExecutionStatus.FAILED
    )
    assert (
        losing.observation.source
        == "manager_lifecycle_authority"
    )


def test_concurrent_terminal_attempts_have_one_winner():
    registry, execution_id = make_registry()

    commit_authorized_transition(
        registry,
        execution_id,
        ExecutionStatus.RUNNING,
        expected_version=0,
        operation_id="concurrent-start-1",
    )

    barrier = Barrier(3)
    results = []
    errors = []
    result_lock = Lock()

    def attempt_terminal(
        target_status,
        operation_id,
    ):
        try:
            barrier.wait(timeout=5)

            result = commit_authorized_transition(
                registry,
                execution_id,
                target_status,
                expected_version=1,
                operation_id=operation_id,
            )

            with result_lock:
                results.append(result)
        except BaseException as error:
            with result_lock:
                errors.append(error)

    threads = (
        Thread(
            target=attempt_terminal,
            args=(
                ExecutionStatus.COMPLETED,
                "concurrent-completion-1",
            ),
        ),
        Thread(
            target=attempt_terminal,
            args=(
                ExecutionStatus.FAILED,
                "concurrent-failure-1",
            ),
        ),
    )

    for thread in threads:
        thread.start()

    barrier.wait(timeout=5)

    for thread in threads:
        thread.join(timeout=5)

    assert all(not thread.is_alive() for thread in threads)
    assert errors == []
    assert len(results) == 2

    applied = [
        result
        for result in results
        if result.disposition.value == "applied"
    ]
    losing = [
        result
        for result in results
        if (
            result.disposition.value
            == "conflicting_terminal_attempt"
        )
    ]

    assert len(applied) == 1
    assert len(losing) == 1

    winner = applied[0]
    loser = losing[0]
    stored = registry.get(execution_id)

    assert winner.applied is True
    assert winner.execution.state_version == 2
    assert (
        winner.execution.status
        in {
            ExecutionStatus.COMPLETED,
            ExecutionStatus.FAILED,
        }
    )

    assert loser.applied is False
    assert loser.observation is not None
    assert loser.observation.rejected_at_version == 2
    assert (
        loser.observation.attempted_status
        != winner.execution.status
    )

    assert stored == winner.execution
    assert stored is not None
    assert stored.state_version == 2
