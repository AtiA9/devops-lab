"""TaskBoard API - a small task list service.

This is the application the DevOps stages are built around. You do not need to change
how it works; you package it (Docker), test and ship it (CI/CD), run it (AWS, Kubernetes),
watch it (Prometheus) and secure it (DevSecOps).
"""
import os
import secrets
import sqlite3
import time

from flask import Flask, g, jsonify, request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

app = Flask(__name__)
# stage 8: the secret comes from the environment (a random one if it is not set)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
DB_PATH = os.environ.get("DB_PATH", "taskboard.db")


def get_db():
    """One SQLite connection per request; the table is created on first use."""
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute(
            "CREATE TABLE IF NOT EXISTS tasks ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, done INTEGER NOT NULL DEFAULT 0)"
        )
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


# stage 7: request count by endpoint and status, and response time (p95/p99)
REQUESTS = Counter("http_requests_total", "HTTP requests", ["method", "endpoint", "status"])
LATENCY = Histogram("http_request_duration_seconds", "HTTP request duration", ["endpoint"])


@app.before_request
def start_timer():
    g.start = time.perf_counter()


@app.after_request
def record_metrics(response):
    endpoint = request.url_rule.rule if request.url_rule else "unknown"
    if endpoint != "/metrics":
        REQUESTS.labels(request.method, endpoint, str(response.status_code)).inc()
        LATENCY.labels(endpoint).observe(time.perf_counter() - g.get("start", time.perf_counter()))
    return response


@app.get("/metrics")
def metrics():
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}


def to_dict(row):
    return {"id": row["id"], "title": row["title"], "done": bool(row["done"])}


@app.get("/health")
def health():
    """Used by Docker, load balancers and Kubernetes probes. Checks the database too."""
    get_db().execute("SELECT 1")
    return jsonify(status="ok")


@app.get("/tasks")
def list_tasks():
    rows = get_db().execute("SELECT * FROM tasks ORDER BY id").fetchall()
    return jsonify([to_dict(r) for r in rows])


@app.post("/tasks")
def create_task():
    data = request.get_json(silent=True) or {}
    title = str(data.get("title", "")).strip()
    if not title or len(title) > 200:
        return jsonify(error="title is required (1-200 characters)"), 400
    db = get_db()
    cur = db.execute("INSERT INTO tasks (title) VALUES (?)", (title,))
    db.commit()
    row = db.execute("SELECT * FROM tasks WHERE id = ?", (cur.lastrowid,)).fetchone()
    return jsonify(to_dict(row)), 201


@app.patch("/tasks/<int:task_id>")
def update_task(task_id):
    data = request.get_json(silent=True) or {}
    if "done" not in data:
        return jsonify(error="field 'done' is required"), 400
    db = get_db()
    cur = db.execute("UPDATE tasks SET done = ? WHERE id = ?", (1 if data["done"] else 0, task_id))
    db.commit()
    if cur.rowcount == 0:
        return jsonify(error="task not found"), 404
    row = db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return jsonify(to_dict(row))


@app.delete("/tasks/<int:task_id>")
def delete_task(task_id):
    db = get_db()
    cur = db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    db.commit()
    if cur.rowcount == 0:
        return jsonify(error="task not found"), 404
    return "", 204


if __name__ == "__main__":
    # stage 8: no debug mode; for local runs only - the container uses gunicorn
    app.run(host="127.0.0.1", port=5000)
