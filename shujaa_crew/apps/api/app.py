from __future__ import annotations

from flask import Flask, jsonify, request

from core.manager.service import ShujaaManager


app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024

manager = ShujaaManager()


@app.get("/health")
def health():
    return jsonify({
        "status": "healthy",
        "service": "shujaa-api",
    })


@app.post("/shujaa-task")
def handle_task():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "status": "error",
            "message": "يجب إرسال بيانات JSON صحيحة.",
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
