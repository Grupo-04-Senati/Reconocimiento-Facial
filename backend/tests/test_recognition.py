from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_reconocer_sin_imagen():
    response = client.post("/api/reconocimiento")
    assert response.status_code == 422


def test_historial():
    response = client.get("/api/reconocimiento/historial")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "historial" in data
