"""API tests. Stage 4 runs these in CI: `pytest` from the project-taskboard folder."""
import pytest

from app.app import app as flask_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr("app.app.DB_PATH", str(tmp_path / "test.db"))
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.get_json() == {"status": "ok"}


def test_create_and_list(client):
    r = client.post("/tasks", json={"title": "Write Dockerfile"})
    assert r.status_code == 201
    assert r.get_json()["title"] == "Write Dockerfile"
    assert [t["title"] for t in client.get("/tasks").get_json()] == ["Write Dockerfile"]


def test_title_is_required(client):
    assert client.post("/tasks", json={}).status_code == 400
    assert client.post("/tasks", json={"title": "x" * 201}).status_code == 400


def test_mark_done(client):
    task_id = client.post("/tasks", json={"title": "Ship it"}).get_json()["id"]
    r = client.patch(f"/tasks/{task_id}", json={"done": True})
    assert r.status_code == 200 and r.get_json()["done"] is True


def test_delete(client):
    task_id = client.post("/tasks", json={"title": "Temp"}).get_json()["id"]
    assert client.delete(f"/tasks/{task_id}").status_code == 204
    assert client.delete(f"/tasks/{task_id}").status_code == 404
