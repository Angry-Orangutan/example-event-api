from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_event_success():
    response = client.post("/event", json={"name": "Midnite"})
    assert response.status_code == 200
    assert response.json() == {"hello": "Midnite"}


def test_event_missing_name():
    response = client.post("/event", json={})
    assert response.status_code == 422  # Validation error
