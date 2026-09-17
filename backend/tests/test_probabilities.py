from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_prediccion():
    response = client.post(
        "/api/probabilidades/prediccion",
        json={
            "similitud": 0.85,
            "distancia": 0.35,
            "calidad_imagen": 0.9,
            "iluminacion": 0.7,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "probabilidad_calibrada" in data
    assert 0.0 <= data["probabilidad_calibrada"] <= 1.0


def test_estadisticas():
    response = client.get("/api/probabilidades/estadisticas")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "estadisticas" in data
