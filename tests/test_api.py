import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import init_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    init_db()


def test_get_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_get_health_readiness():
    response = client.get("/health/ready")
    assert response.status_code == 200
    assert "status" in response.json()


def test_get_runs_includes_seed():
    response = client.get("/api/runs")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    names = [r["sandbox_name"] for r in data]
    assert "sbx-seeddemo1" in names


def test_post_run_valid():
    uid = uuid.uuid4().hex[:8]
    payload = {
        "run_id": f"test-valid-{uid}",
        "sandbox_name": f"sbx-valid{uid}",
        "problem_id": "benign_task",
        "state": "created",
        "execution_target": "celesto_sandbox"
    }
    response = client.post("/api/runs", json=payload)
    assert response.status_code == 201
    stored = response.json()
    assert stored["run_id"] == payload["run_id"]
    assert stored["sandbox_name"] == payload["sandbox_name"]
    assert stored["execution_target"] == "celesto_sandbox"


def test_post_run_duplicate_id():
    uid = uuid.uuid4().hex[:8]
    payload = {
        "run_id": f"test-dup-{uid}",
        "sandbox_name": f"sbx-dup{uid}",
        "problem_id": "benign_task",
        "state": "created",
        "execution_target": "celesto_sandbox"
    }
    res1 = client.post("/api/runs", json=payload)
    assert res1.status_code == 201

    res2 = client.post("/api/runs", json=payload)
    assert res2.status_code == 400


def test_post_run_invalid_execution_target():
    uid = uuid.uuid4().hex[:8]
    payload = {
        "run_id": f"test-target-{uid}",
        "sandbox_name": f"sbx-target{uid}",
        "problem_id": "benign_task",
        "state": "created",
        "execution_target": "host"
    }
    response = client.post("/api/runs", json=payload)
    assert response.status_code == 400


def test_post_run_malformed_sandbox_name():
    uid = uuid.uuid4().hex[:8]
    payload = {
        "run_id": f"test-badname-{uid}",
        "sandbox_name": "sbx-short",
        "problem_id": "benign_task",
        "state": "created",
        "execution_target": "celesto_sandbox"
    }
    response = client.post("/api/runs", json=payload)
    assert response.status_code == 400


def test_post_run_invalid_state():
    uid = uuid.uuid4().hex[:8]
    payload = {
        "run_id": f"test-badstate-{uid}",
        "sandbox_name": f"sbx-badst{uid}",
        "problem_id": "benign_task",
        "state": "unknown_state",
        "execution_target": "celesto_sandbox"
    }
    response = client.post("/api/runs", json=payload)
    assert response.status_code == 400
