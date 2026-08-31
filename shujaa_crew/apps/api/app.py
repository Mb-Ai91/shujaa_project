from __future__ import annotations

import atexit
import hmac
import os
import time
from uuid import uuid4

from dotenv import load_dotenv
from flask import Flask, jsonify, request

from adapters.agents.factory import build_agent_executor
from adapters.crewai.runner import CrewAIRunner
from adapters.mock.runner import MockRunner
from adapters.storage.sqlite_task_store import SQLiteTaskStore
from core.agents.bootstrap import build_agent_registry
from core.agents.executor_registry import AgentExecutorRegistry
from core.manager.service import ShujaaManager
from core.policy.contracts import (
    ActorRef,
    AuthorizationContext,
    AuthorizationRequest,
    ResourceRef,
)
from core.policy.evaluator import (
    SinglePrincipalCancelEvaluator,
    SinglePrincipalSubmitEvaluator,
)
from core.tasks.store import InMemoryTaskStore


load_dotenv()

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024

runner_name = os.getenv("SHUJAA_RUNNER", "crewai").strip().lower()

if runner_name == "mock":
    runner = MockRunner()
elif runner_name == "crewai":
    runner = CrewAIRunner()
else:
    raise RuntimeError(
        f"Unsupported SHUJAA_RUNNER: {runner_name}"
    )

task_store_name = os.getenv(
    "SHUJAA_TASK_STORE",
    "memory",
).strip().lower()

if task_store_name == "memory":
    task_store = InMemoryTaskStore()
elif task_store_name == "sqlite":
    task_store = SQLiteTaskStore()
else:
    raise RuntimeError(
        f"Unsupported SHUJAA_TASK_STORE: {task_store_name}"
    )

agent_registry = build_agent_registry(
    "config/agents"
)

agent_executor_registry = AgentExecutorRegistry()

API_SERVICE_ACTOR = ActorRef(
    actor_type="service",
    actor_id="shujaa-local-api-service",
)
cancel_authorization_evaluator = SinglePrincipalCancelEvaluator(
    principal=API_SERVICE_ACTOR,
    policy_version="stage7.1-local-api-v1",
)
submit_authorization_evaluator = SinglePrincipalSubmitEvaluator(
    principal=API_SERVICE_ACTOR,
    policy_version="stage7.2-local-api-v1",
)

for agent in agent_registry.list():
    agent_executor_registry.register(
        agent.agent_id,
        build_agent_executor(agent),
    )

manager = ShujaaManager(
    crew_runner=runner,
    task_store=task_store,
    agent_registry=agent_registry,
    agent_executor_registry=agent_executor_registry,
    cancel_authorization_evaluator=(
        cancel_authorization_evaluator
    ),
    submit_authorization_evaluator=(
        submit_authorization_evaluator
    ),
)


_SUBMIT_ERROR_STATUS = {
    "AUTHORIZATION_REQUEST_INVALID": 400,
    "POLICY_DENIED": 403,
    "SUBMIT_OPERATION_REUSED": 409,
    "EVALUATOR_UNAVAILABLE": 503,
    "AUDIT_UNAVAILABLE": 503,
}


def _new_submit_authorization_request() -> AuthorizationRequest:
    operation_id = f"op-submit-request-{uuid4()}"
    return AuthorizationRequest(
        actor=API_SERVICE_ACTOR,
        action="work.submit",
        resource=ResourceRef(
            resource_type="work_submission",
            resource_id=operation_id,
        ),
        context=AuthorizationContext(
            request_id=f"request-submit-{uuid4()}",
            operation_id=operation_id,
        ),
    )


def _submit_error_status(error: ValueError) -> int | None:
    return _SUBMIT_ERROR_STATUS.get(
        getattr(error, "reason_code", None)
    )


def is_authorized() -> bool:
    expected_key = os.getenv("SHUJAA_API_KEY", "")
    provided_key = request.headers.get("X-Shujaa-Key", "")

    if not expected_key or not provided_key:
        return False

    return hmac.compare_digest(provided_key, expected_key)


@app.post("/agents/<agent_id>/execute")
def execute_agent(agent_id: str):
    if not is_authorized():
        return jsonify({
            "status": "error",
            "message": "Unauthorized.",
        }), 401

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "status": "error",
            "message": "Invalid JSON payload.",
        }), 400

    task = data.get("task")

    if not isinstance(task, str):
        return jsonify({
            "status": "error",
            "message": "Task must be a string.",
        }), 400

    try:
        submitted = manager.submit(
            task,
            authorization_request=(
                _new_submit_authorization_request()
            ),
            requested_agent_id=agent_id,
        )
    except ValueError as error:
        message = str(error)

        mapped_status = _submit_error_status(error)
        if mapped_status is not None:
            status_code = mapped_status
        elif message.startswith("Agent not found:"):
            status_code = 404
        else:
            status_code = 400

        return jsonify({
            "status": "error",
            "message": message,
        }), status_code

    task_id = submitted["task_id"]
    deadline = time.monotonic() + manager.TASK_TIMEOUT_SECONDS

    while time.monotonic() < deadline:
        tracked = manager.get_task(task_id)

        if tracked is not None and tracked["status"] in {
            "completed",
            "failed",
            "timed_out",
            "cancelled",
        }:
            break

        time.sleep(0.01)
    else:
        return jsonify({
            "status": "error",
            "message": "Agent execution did not finish in time.",
            "work_id": submitted["work_id"],
            "task_id": task_id,
            "execution_id": submitted["execution_id"],
        }), 504

    if tracked["status"] != "completed":
        return jsonify({
            "status": "error",
            "message": tracked.get("error") or (
                f"Agent execution ended with "
                f"status: {tracked['status']}"
            ),
            "work_id": submitted["work_id"],
            "task_id": task_id,
            "execution_id": submitted["execution_id"],
        }), 400

    return jsonify({
        "status": "completed",
        "agent_id": agent_id,
        "result": tracked["result"],
        "work_id": submitted["work_id"],
        "task_id": task_id,
        "execution_id": submitted["execution_id"],
    }), 200


@app.get("/agents")
def list_agents():
    if not is_authorized():
        return jsonify({
            "status": "error",
            "message": "Unauthorized.",
        }), 401

    return jsonify([
        {
            "agent_id": agent.agent_id,
            "name": agent.name,
            "description": agent.description,
            "capabilities": list(agent.capabilities),
            "enabled": agent.enabled,
        }
        for agent in agent_registry.list()
    ]), 200


@app.get("/health")
def health():
    return jsonify({
        "status": "healthy",
        "service": "shujaa-api",
    })


@app.post("/shujaa-task")
def handle_task():
    if not is_authorized():
        return jsonify({
            "status": "error",
            "message": "Unauthorized.",
        }), 401

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "status": "error",
            "message": "Invalid JSON payload.",
        }), 400

    try:
        return jsonify(
            manager.submit(
                data.get("command"),
                authorization_request=(
                    _new_submit_authorization_request()
                ),
            )
        ), 202

    except ValueError as error:
        return jsonify({
            "status": "error",
            "message": str(error),
        }), _submit_error_status(error) or 400

    except RuntimeError as error:
        return jsonify({
            "status": "error",
            "message": str(error),
        }), 500


@app.post("/tasks/<task_id>/cancel")
def cancel_task(task_id: str):
    if not is_authorized():
        return jsonify({
            "status": "error",
            "message": "Unauthorized.",
        }), 401

    try:
        cancel_operation_id = (
            f"op-cancel-request-{uuid4()}"
        )
        cleanup_operation_id = (
            f"op-cancel-cleanup-{uuid4()}"
        )
        authorization_request = AuthorizationRequest(
            actor=API_SERVICE_ACTOR,
            action="task.cancel",
            resource=ResourceRef(
                resource_type="task",
                resource_id=task_id,
            ),
            context=AuthorizationContext(
                request_id=f"request-cancel-{uuid4()}",
                operation_id=cancel_operation_id,
            ),
        )
        return jsonify(
            manager.cancel_task(
                task_id,
                authorization_request=authorization_request,
                cancel_operation_id=(
                    cancel_operation_id
                ),
                cleanup_operation_id=(
                    cleanup_operation_id
                ),
            )
        ), 200
    except ValueError as error:
        message = str(error)
        reason_code = getattr(error, "reason_code", None)
        if message == "Task not found.":
            status_code = 404
        elif reason_code == "POLICY_DENIED":
            status_code = 403
        elif reason_code in {
            "EVALUATOR_UNAVAILABLE",
            "AUDIT_UNAVAILABLE",
        }:
            status_code = 503
        else:
            status_code = 409

        return jsonify({
            "status": "error",
            "message": message,
            "error_code": reason_code,
        }), status_code


@app.get("/tasks/<task_id>")
def get_task(task_id: str):
    if not is_authorized():
        return jsonify({
            "status": "error",
            "message": "Unauthorized.",
        }), 401

    task = manager.get_task(task_id)

    if task is None:
        return jsonify({
            "status": "error",
            "message": "Task not found.",
        }), 404

    return jsonify(task), 200


if __name__ == "__main__":
    # تنظيف أي عمليات CrewAI متبقية من جلسة سابقة.
    manager.cleanup_registered_processes(
        cleanup_operation_id=f"op-startup-cleanup-{uuid4()}"
    )

    # تنظيف العمليات المسجلة عند الإغلاق الطبيعي.
    atexit.register(
        lambda: manager.cleanup_registered_processes(
            cleanup_operation_id=f"op-shutdown-cleanup-{uuid4()}"
        )
    )

    app.run(host="0.0.0.0", port=5000, debug=False)
