import pytest
from fastapi.testclient import TestClient

from app import main as api


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(api, "DB_PATH", tmp_path / "todos.sqlite")
    with TestClient(api.app) as test_client:
        yield test_client


def test_health_and_metrics(client):
    assert client.get("/health/live").json() == {"status": "ok"}
    assert client.get("/health/ready").json() == {"status": "ready"}
    assert client.get("/todos/404").status_code == 404
    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    assert "http_requests_total" in metrics.text
    assert 'path="/todos/{todo_id}"' in metrics.text


def test_todo_create_read_update_delete(client):
    created = client.post("/todos", json={"title": "  Ship the project  "})
    assert created.status_code == 201
    todo = created.json()
    assert todo["title"] == "Ship the project"
    assert todo["completed"] is False

    todo_id = todo["id"]
    assert client.get("/todos").json() == [todo]
    assert client.get(f"/todos/{todo_id}").json() == todo

    renamed = client.patch(f"/todos/{todo_id}", json={"title": "Review release"})
    assert renamed.status_code == 200
    assert renamed.json()["title"] == "Review release"

    completed = client.patch(f"/todos/{todo_id}", json={"completed": True})
    assert completed.status_code == 200
    assert completed.json()["completed"] is True

    assert client.delete(f"/todos/{todo_id}").status_code == 204
    assert client.get(f"/todos/{todo_id}").status_code == 404
    assert client.delete(f"/todos/{todo_id}").status_code == 404


def test_rejects_blank_titles_and_empty_update(client):
    assert client.post("/todos", json={"title": "   "}).status_code == 422
    created = client.post("/todos", json={"title": "valid"})
    todo_id = created.json()["id"]
    assert client.patch(f"/todos/{todo_id}", json={"title": "   "}).status_code == 422
    assert client.patch(f"/todos/{todo_id}", json={"title": None}).status_code == 422
    assert (
        client.patch(f"/todos/{todo_id}", json={"completed": None}).status_code == 422
    )
    assert client.patch(f"/todos/{todo_id}", json={}).status_code == 400
