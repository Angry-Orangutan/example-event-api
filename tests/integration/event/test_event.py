import pytest
from fastapi.testclient import TestClient
from httpx import Response

from app.main import app
from app.services.state_manager import StateManager

client: TestClient = TestClient(app)


@pytest.fixture(autouse=True)
def clear_state() -> None:
    """Clear state manager before each test"""
    StateManager().clear()


def test_deposit_event() -> None:
    """Test basic deposit event"""
    response: Response = client.post("/event", json={"type": "deposit", "amount": "42.00", "user_id": 1, "t": 10})
    assert response.status_code == 200
    response_json = response.json()
    print(response_json)
    assert response_json["alert"] is False
    assert response_json["user_id"] == 1
    assert response_json["alert_codes"] == []


def test_withdrawal_event() -> None:
    """Test basic withdrawal event"""
    response: Response = client.post("/event", json={"type": "withdraw", "amount": "42.00", "user_id": 1, "t": 10})
    assert response.status_code == 200
    response_json = response.json()
    print(response_json)
    assert response_json["alert"] is False
    assert response_json["user_id"] == 1
    assert response_json["alert_codes"] == []


def test_event_invalid_request() -> None:
    """Test invalid request handling"""
    response: Response = client.post("/event", json={})
    assert response.status_code == 422  # Validation error
