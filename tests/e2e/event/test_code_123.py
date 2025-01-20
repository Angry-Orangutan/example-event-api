import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.alert import AlertCode
from app.models.event import EventType
from app.services.state_manager import StateManager

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_state() -> None:
    """Clear state manager before each test"""
    StateManager().clear()


def test_alert_123_triggered():
    """Test that Alert 123 is triggered when deposits exceed 200 in 30 seconds."""
    # First deposit
    response = client.post(
        "/event",
        json={"type": EventType.DEPOSIT, "amount": "100.00", "user_id": 1, "t": 100},
    )
    assert response.status_code == 200
    assert response.json()["alert_codes"] == []

    # Second deposit within 30 seconds
    response = client.post(
        "/event",
        json={"type": EventType.DEPOSIT, "amount": "150.00", "user_id": 1, "t": 120},
    )
    assert response.status_code == 200
    assert AlertCode.ALERT_123.value in response.json()["alert_codes"]


def test_alert_123_not_triggered_under_200():
    """Test that Alert 123 is not triggered when deposits are under 200."""
    # First deposit
    response = client.post(
        "/event",
        json={"type": EventType.DEPOSIT, "amount": "50.00", "user_id": 1, "t": 100},
    )
    assert response.status_code == 200
    assert response.json()["alert_codes"] == []

    # Second deposit within 30 seconds
    response = client.post(
        "/event",
        json={"type": EventType.DEPOSIT, "amount": "40.00", "user_id": 1, "t": 110},
    )
    assert response.status_code == 200
    assert response.json()["alert_codes"] == []


def test_alert_123_not_triggered_outside_window():
    """Test that Alert 123 is not triggered when deposits are spread out or under limit."""
    # First deposit
    response = client.post(
        "/event",
        json={"type": EventType.DEPOSIT, "amount": "100.00", "user_id": 2, "t": 100},
    )
    assert response.status_code == 200
    assert response.json()["alert_codes"] == []

    # Second deposit after 30 seconds
    response = client.post(
        "/event",
        json={"type": EventType.DEPOSIT, "amount": "150.00", "user_id": 2, "t": 140},
    )
    assert response.status_code == 200
    assert AlertCode.ALERT_123.value not in response.json()["alert_codes"]


def test_alert_123_triggered_by_single_deposit():
    """Test that Alert 123 is triggered when a single deposit of 200 is made."""
    # First deposit
    response = client.post(
        "/event",
        json={"type": EventType.DEPOSIT, "amount": "200.01", "user_id": 1, "t": 100},
    )
    assert response.status_code == 200
    assert AlertCode.ALERT_123.value in response.json()["alert_codes"]


def test_alert_123_not_triggered_by_200():
    """Test that Alert 123 is not triggered when a single deposit of 200 is made."""
    # First deposit
    response = client.post(
        "/event",
        json={"type": EventType.DEPOSIT, "amount": "200.00", "user_id": 1, "t": 100},
    )
    assert response.status_code == 200
    assert AlertCode.ALERT_123.value not in response.json()["alert_codes"]
