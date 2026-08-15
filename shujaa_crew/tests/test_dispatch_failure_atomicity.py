import pytest

from core.manager.service import ShujaaManager


class UnusedRunner:
    def start(self, command):
        raise AssertionError("Runner must not be called.")


class RejectingDispatcher:
    def __init__(self):
        self.request = None

    def dispatch(self, request):
        self.request = request
        raise ValueError("route rejected")


def test_dispatch_rejection_persists_no_partial_records():
    dispatcher = RejectingDispatcher()
    manager = ShujaaManager(
        crew_runner=UnusedRunner(),
        execution_dispatcher=dispatcher,
    )

    with pytest.raises(ValueError, match="route rejected"):
        manager.submit("test task")

    request = dispatcher.request

    assert request is not None
    assert manager.work_registry.get(request.work_id) is None
    assert manager.task_store.get(request.task_id) is None
    assert (
        manager.execution_registry.get(request.execution_id)
        is None
    )
