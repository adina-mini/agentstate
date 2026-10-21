from fastapi.testclient import TestClient
from agentgate.api.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "AgentGate"


def test_list_sources_endpoint():
    response = client.get("/api/sources")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_evals_endpoint():
    response = client.get("/api/evals")
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "recent_logs" in data
