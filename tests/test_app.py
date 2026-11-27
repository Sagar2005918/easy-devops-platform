import pytest
from app import app, TASKS

@pytest.fixture()
def client():
    TASKS.clear()
    app.config.update(TESTING=True)
    return app.test_client()

def test_health_and_readiness(client):
    assert client.get("/health").json["status"] == "ok"
    assert client.get("/ready").json["status"] == "ready"

def test_create_and_list_tasks(client):
    created = client.post("/tasks", json={"title": "Ship safely"})
    assert created.status_code == 201
    assert created.json["title"] == "Ship safely"
    assert client.get("/tasks").json == [created.json]

def test_rejects_empty_title(client):
    assert client.post("/tasks", json={"title": "  "}).status_code == 400

def test_delete_task(client):
    task_id = client.post("/tasks", json={"title": "Temporary"}).json["id"]
    assert client.delete(f"/tasks/{task_id}").status_code == 204
    assert client.get(f"/tasks/{task_id}").status_code == 404

def test_security_headers_and_metrics(client):
    response = client.get("/")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert "app_requests_total" in client.get("/metrics").text
