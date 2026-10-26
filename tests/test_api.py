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


def test_document_upload_inspect_and_delete():
    # Test uploading a text document
    sample_content = b"# Nebula Engine Spec\nNebula is a hyper-dimensional propulsion engine operating at 1.4 petawatts."
    files = {"file": ("nebula_spec.md", sample_content, "text/markdown")}
    
    upload_res = client.post("/api/sources/upload", files=files)
    assert upload_res.status_code == 200
    source_data = upload_res.json()
    source_id = source_data["id"]
    assert "File: nebula_spec.md" in source_data["name"]

    # Test source details inspection
    details_res = client.get(f"/api/sources/{source_id}")
    assert details_res.status_code == 200
    details = details_res.json()
    assert len(details.get("preview_chunks", [])) >= 1

    # Test deleting source
    del_res = client.delete(f"/api/sources/{source_id}")
    assert del_res.status_code == 200
    assert "removed successfully" in del_res.json()["message"]

