from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_model_status():
    response = client.get("/api/models/status")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "models" in data
