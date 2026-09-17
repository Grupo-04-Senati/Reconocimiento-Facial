from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_listar_personas():
    response = client.get("/api/personas")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "personas" in data


def test_registrar_persona_campos_requeridos():
    response = client.post("/api/personas", data={"nombre": "Test"})
    assert response.status_code == 422


def test_obtener_persona_no_encontrada():
    response = client.get("/api/personas/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
