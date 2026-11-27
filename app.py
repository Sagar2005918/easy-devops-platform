"""Tiny task API used to demonstrate a complete delivery pipeline."""
import json
import logging
import os
import time
import uuid
from datetime import datetime, timezone

from flask import Flask, jsonify, request

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024

# JSON logs make container output easy to index in Loki or another log backend.
class JsonFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname.lower(),
            "message": record.getMessage(),
            "service": "easy-devops-task-api",
        }
        if hasattr(record, "event"):
            payload.update(record.event)
        return json.dumps(payload)

handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
app.logger.handlers = [handler]
app.logger.setLevel(logging.INFO)

TASKS = {}
REQUEST_COUNT = 0
STATUS_COUNTS = {}
STARTED_AT = time.time()

@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = "no-store"
    return response

@app.before_request
def count_request():
    global REQUEST_COUNT
    REQUEST_COUNT += 1

@app.after_request
def count_status(response):
    status = response.status_code
    STATUS_COUNTS[status] = STATUS_COUNTS.get(status, 0) + 1
    return response

@app.get("/")
def index():
    return jsonify({
        "name": "Easy DevOps Task API",
        "message": "A tiny app for learning a full software delivery lifecycle.",
        "routes": ["GET /health", "GET /ready", "GET /tasks", "POST /tasks", "GET /tasks/<id>", "DELETE /tasks/<id>", "GET /metrics"],
    })

@app.get("/health")
def health():
    return jsonify({"status": "ok"})

@app.get("/ready")
def ready():
    return jsonify({"status": "ready", "uptime_seconds": round(time.time() - STARTED_AT, 1)})

@app.get("/tasks")
def list_tasks():
    return jsonify(list(TASKS.values()))

@app.post("/tasks")
def create_task():
    body = request.get_json(silent=True) or {}
    title = body.get("title")
    if not isinstance(title, str) or not title.strip():
        return jsonify({"error": "title is required"}), 400
    task = {"id": str(uuid.uuid4()), "title": title.strip(), "done": False}
    TASKS[task["id"]] = task
    app.logger.info("task_created", extra={"event": {"task_id": task["id"]}})
    return jsonify(task), 201

@app.get("/tasks/<task_id>")
def get_task(task_id):
    task = TASKS.get(task_id)
    if not task:
        return jsonify({"error": "task not found"}), 404
    return jsonify(task)

@app.delete("/tasks/<task_id>")
def delete_task(task_id):
    if TASKS.pop(task_id, None) is None:
        return jsonify({"error": "task not found"}), 404
    app.logger.info("task_deleted", extra={"event": {"task_id": task_id}})
    return "", 204

@app.get("/metrics")
def metrics():
    body = "# HELP app_requests_total Total HTTP requests handled.\n# TYPE app_requests_total counter\n"
    body += f"app_requests_total {REQUEST_COUNT}\n"
    for status, count in sorted(STATUS_COUNTS.items()):
        body += f'app_responses_total{{status="{status}"}} {count}\n'
    body += "# HELP app_uptime_seconds Seconds since process start.\n# TYPE app_uptime_seconds gauge\n"
    body += f"app_uptime_seconds {time.time() - STARTED_AT:.1f}\n"
    return body, 200, {"Content-Type": "text/plain; version=0.0.4; charset=utf-8"}

if __name__ == "__main__":
    app.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", "8080")))
