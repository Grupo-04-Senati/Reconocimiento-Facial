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
    response = client.get("/api/modelos/status")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "models" in data


def test_model_metricas_no_model():
    response = client.get("/api/modelos/metricas")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "trained" in data


def test_list_personas():
    response = client.get("/api/personas")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "personas" in data


def test_prediction():
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
    assert "total_reconocimientos" in data["estadisticas"]


def test_historial():
    response = client.get("/api/reconocimiento/historial")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "historial" in data
