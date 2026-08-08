from __future__ import annotations

import atexit
import hmac
import os

from dotenv import load_dotenv
from flask import Flask, jsonify, request

from adapters.crewai.runner import CrewAIRunner
from adapters.mock.runner import MockRunner
from adapters.storage.sqlite_task_store import SQLiteTaskStore
from core.agents.bootstrap import build_agent_registry
from core.manager.service import ShujaaManager
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

manager = ShujaaManager(
    crew_runner=runner,
    task_store=task_store,
)


def is_authorized() -> bool:
    expected_key = os.getenv("SHUJAA_API_KEY", "")
    provided_key = request.headers.get("X-Shujaa-Key", "")

    if not expected_key or not provided_key:
        return False

    return hmac.compare_digest(provided_key, expected_key)


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
        return jsonify(manager.submit(data.get("command"))), 202

    except ValueError as error:
        return jsonify({
            "status": "error",
            "message": str(error),
        }), 400

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
        return jsonify(manager.cancel_task(task_id)), 200
    except ValueError as error:
        message = str(error)
        status_code = 404 if message == "Task not found." else 409

        return jsonify({
            "status": "error",
            "message": message,
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
    manager.cleanup_registered_processes()

    # تنظيف العمليات المسجلة عند الإغلاق الطبيعي.
    atexit.register(manager.cleanup_registered_processes)

    app.run(host="0.0.0.0", port=5000, debug=False)
