from __future__ import annotations

import hmac
import os

from dotenv import load_dotenv
from flask import Flask, jsonify, request

from core.manager.service import ShujaaManager


load_dotenv()

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024

manager = ShujaaManager()


def is_authorized() -> bool:
    expected_key = os.getenv("SHUJAA_API_KEY", "")
    provided_key = request.headers.get("X-Shujaa-Key", "")

    if not expected_key or not provided_key:
        return False

    return hmac.compare_digest(provided_key, expected_key)


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
        result = manager.submit(data.get("command"))
        return jsonify(result), 202

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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
