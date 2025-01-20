import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.alert import AlertCode
from app.models.event import EventType
from tests.utils.fixtures import clear_state  # noqa: F401

client = TestClient(app)


@pytest.mark.usefixtures("clear_state")
def test_alert_123_triggered() -> None:
    """Test that Alert 123 is triggered when deposits exceed 200 in 30 seconds."""
    # First deposit
    response = client.post(
        "/event",
        json={"type": EventType.DEPOSIT, "amount": "100.00", "user_id": 1, "t": 10},
    )
    assert response.status_code == 200
    assert response.json()["alert_codes"] == []

    # Second deposit within 30 seconds
    response = client.post(
        "/event",
        json={"type": EventType.DEPOSIT, "amount": "150.00", "user_id": 1, "t": 20},
    )
    assert response.status_code == 200
    assert AlertCode.ALERT_123.value in response.json()["alert_codes"]


@pytest.mark.usefixtures("clear_state")
def test_alert_123_not_triggered_under_200() -> None:
    """Test that Alert 123 is not triggered when deposits are under 200."""
    # First deposit
    response = client.post(
        "/event",
        json={"type": EventType.DEPOSIT, "amount": "50.00", "user_id": 1, "t": 10},
    )
    assert response.status_code == 200
    assert response.json()["alert_codes"] == []

    # Second deposit within 30 seconds
    response = client.post(
        "/event",
        json={"type": EventType.DEPOSIT, "amount": "40.00", "user_id": 1, "t": 20},
    )
    assert response.status_code == 200
    assert response.json()["alert_codes"] == []


@pytest.mark.usefixtures("clear_state")
def test_alert_123_not_triggered_outside_window() -> None:
    """Test that Alert 123 is not triggered when deposits are spread out or under limit."""
    # First deposit
    response = client.post(
        "/event",
        json={"type": EventType.DEPOSIT, "amount": "100.00", "user_id": 2, "t": 10},
    )
    assert response.status_code == 200
    assert response.json()["alert_codes"] == []

    # Second deposit after 30 seconds
    response = client.post(
        "/event",
        json={"type": EventType.DEPOSIT, "amount": "150.00", "user_id": 2, "t": 50},
    )
    assert response.status_code == 200
    assert AlertCode.ALERT_123.value not in response.json()["alert_codes"]


@pytest.mark.usefixtures("clear_state")
def test_alert_123_triggered_by_single_deposit() -> None:
    """Test that Alert 123 is triggered when a single deposit of 200 is made."""
    # First deposit
    response = client.post(
        "/event",
        json={"type": EventType.DEPOSIT, "amount": "200.01", "user_id": 1, "t": 10},
    )
    assert response.status_code == 200
    assert AlertCode.ALERT_123.value in response.json()["alert_codes"]


@pytest.mark.usefixtures("clear_state")
def test_alert_123_not_triggered_by_200() -> None:
    """Test that Alert 123 is not triggered when a single deposit of 200 is made."""
    # First deposit
    response = client.post(
        "/event",
        json={"type": EventType.DEPOSIT, "amount": "200.00", "user_id": 1, "t": 10},
    )
    assert response.status_code == 200
    assert AlertCode.ALERT_123.value not in response.json()["alert_codes"]


@pytest.mark.usefixtures("clear_state")
def test_alert_123_window_with_early_timestamp() -> None:
    """Test that Alert 123 correctly handles early timestamps (t=10).

    The rule should look back 30 seconds from the event time (t=10),
    meaning it should consider events from t=0 to t=10.

    The main logic we are testing here, is that the lookback doesn't fail
    when performing a search of "-30" seconds on a timestamp of under 30 seconds.
    """
    # First deposit at t=0 (at window boundary)
    response = client.post(
        "/event",
        json={"type": EventType.DEPOSIT, "amount": "100.00", "user_id": 1, "t": 0},
    )
    assert response.status_code == 200
    assert response.json()["alert_codes"] == []

    # Second deposit at t=5 (inside window)
    response = client.post(
        "/event",
        json={"type": EventType.DEPOSIT, "amount": "50.00", "user_id": 1, "t": 5},
    )
    assert response.status_code == 200
    assert response.json()["alert_codes"] == []

    # Final deposit at t=10 - should trigger alert since total is 250
    response = client.post(
        "/event",
        json={"type": EventType.DEPOSIT, "amount": "100.00", "user_id": 1, "t": 10},
    )
    assert response.status_code == 200
    assert AlertCode.ALERT_123.value in response.json()["alert_codes"]


@pytest.mark.usefixtures("clear_state")
def test_alert_123_triggered_multiple_same_timestamp() -> None:
    """Test that Alert 123 is triggered on 3rd and 4th deposits when all deposits
    have the same timestamp and are 100 each."""
    # First deposit at t=10
    response = client.post(
        "/event",
        json={"type": EventType.DEPOSIT, "amount": "100.00", "user_id": 1, "t": 10},
    )
    assert response.status_code == 200
    assert response.json()["alert_codes"] == []

    # Second deposit at same timestamp
    response = client.post(
        "/event",
        json={"type": EventType.DEPOSIT, "amount": "100.00", "user_id": 1, "t": 10},
    )
    assert response.status_code == 200
    assert response.json()["alert_codes"] == []

    # Third deposit at same timestamp - should trigger alert (total 300)
    response = client.post(
        "/event",
        json={"type": EventType.DEPOSIT, "amount": "100.00", "user_id": 1, "t": 10},
    )
    assert response.status_code == 200
    assert AlertCode.ALERT_123.value in response.json()["alert_codes"]

    # Fourth deposit at same timestamp - should also trigger alert (total 400)
    response = client.post(
        "/event",
        json={"type": EventType.DEPOSIT, "amount": "100.00", "user_id": 1, "t": 10},
    )
    assert response.status_code == 200
    assert AlertCode.ALERT_123.value in response.json()["alert_codes"]
