import pytest
from uuid import uuid4

from core.manager.service import ShujaaManager
from core.policy.contracts import (
    ActorRef,
    AuthorizationContext,
    AuthorizationRequest,
    ResourceRef,
)
from core.policy.evaluator import SinglePrincipalSubmitEvaluator


_SUBMIT_ACTOR = ActorRef(
    actor_type="service",
    actor_id="test-dispatch-failure-submit",
)


def _authorized_submit(manager, command, **kwargs):
    operation_id = f"op-test-dispatch-failure-{uuid4()}"
    manager.submit_authorization_evaluator = (
        SinglePrincipalSubmitEvaluator(
            principal=_SUBMIT_ACTOR,
            policy_version="test-dispatch-failure-submit-v1",
        )
    )
    return manager.submit(
        command,
        authorization_request=AuthorizationRequest(
            actor=_SUBMIT_ACTOR,
            action="work.submit",
            resource=ResourceRef(
                resource_type="work_submission",
                resource_id=operation_id,
            ),
            context=AuthorizationContext(
                request_id=f"request-{operation_id}",
                operation_id=operation_id,
            ),
        ),
        **kwargs,
    )


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
        _authorized_submit(manager, "test task")

    request = dispatcher.request

    assert request is not None
    assert manager.work_registry.get(request.work_id) is None
    assert manager.task_store.get(request.task_id) is None
    assert (
        manager.execution_registry.get(request.execution_id)
        is None
    )
