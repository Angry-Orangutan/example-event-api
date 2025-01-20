import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.alert import AlertCode
from app.services.state_manager import StateManager

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_state() -> None:
    """Clear state manager before each test"""
    StateManager().clear()


def test_three_consecutive_increasing_deposits_triggers_alert():
    """
    Test that three consecutive increasing deposits trigger Alert 300.

    Scenario:
    1. Make first deposit (smallest)
    2. Make second deposit (medium)
    3. Make third deposit (largest)
    4. Verify Alert 300 is triggered on the third deposit
    """
    user_id = 1

    # First deposit (smallest)
    response = client.post("/event", json={"type": "deposit", "amount": "10.00", "user_id": user_id, "t": 1000})
    assert response.status_code == 200
    assert not response.json()["alert"]

    # Second deposit (medium)
    response = client.post("/event", json={"type": "deposit", "amount": "20.00", "user_id": user_id, "t": 2000})
    assert response.status_code == 200
    assert not response.json()["alert"]

    # Third deposit (largest) - should trigger alert
    response = client.post("/event", json={"type": "deposit", "amount": "30.00", "user_id": user_id, "t": 3000})
    assert response.status_code == 200
    assert response.json()["alert"]
    assert AlertCode.ALERT_300.value in [code for code in response.json()["alert_codes"]]


def test_withdrawals_between_deposits_dont_affect_alert():
    """
    Test that withdrawals between deposits don't prevent Alert 300 from triggering.

    Scenario:
    1. Make first deposit
    2. Make a withdrawal
    3. Make second larger deposit
    4. Make another withdrawal
    5. Make third largest deposit
    6. Verify Alert 300 is triggered
    """
    user_id = 2

    # First deposit
    response = client.post("/event", json={"type": "deposit", "amount": "50.00", "user_id": user_id, "t": 1000})
    assert response.status_code == 200

    # Withdrawal in between
    response = client.post("/event", json={"type": "withdraw", "amount": "10.00", "user_id": user_id, "t": 2000})
    assert response.status_code == 200

    # Second deposit (larger)
    response = client.post("/event", json={"type": "deposit", "amount": "75.00", "user_id": user_id, "t": 3000})
    assert response.status_code == 200

    # Another withdrawal
    response = client.post("/event", json={"type": "withdraw", "amount": "20.00", "user_id": user_id, "t": 4000})
    assert response.status_code == 200

    # Third deposit (largest) - should trigger alert
    response = client.post("/event", json={"type": "deposit", "amount": "100.00", "user_id": user_id, "t": 5000})
    assert response.status_code == 200
    assert response.json()["alert"]
    assert AlertCode.ALERT_300.value in [code for code in response.json()["alert_codes"]]


def test_non_increasing_deposits_no_alert():
    """
    Test that non-increasing deposits don't trigger Alert 300.

    Scenario:
    1. Make first deposit
    2. Make second smaller deposit
    3. Make third largest deposit
    4. Verify Alert 300 is not triggered
    """
    user_id = 3

    # First deposit
    response = client.post("/event", json={"type": "deposit", "amount": "50.00", "user_id": user_id, "t": 1000})
    assert response.status_code == 200

    # Second deposit (smaller)
    response = client.post("/event", json={"type": "deposit", "amount": "25.00", "user_id": user_id, "t": 2000})
    assert response.status_code == 200

    # Third deposit (largest)
    response = client.post("/event", json={"type": "deposit", "amount": "100.00", "user_id": user_id, "t": 3000})
    assert response.status_code == 200
    assert not response.json()["alert"]
    assert AlertCode.ALERT_300.value not in [code for code in response.json()["alert_codes"]]


def test_different_users_dont_interfere():
    """
    Test that deposits from different users don't interfere with each other's alerts.

    Scenario:
    1. User 1 makes two increasing deposits
    2. User 2 makes two increasing deposits
    3. User 1 makes third largest deposit
    4. Verify only User 1 triggers Alert 300
    """
    # User 1's first two deposits
    for i, amount in enumerate(["10.00", "20.00"], 1):
        response = client.post("/event", json={"type": "deposit", "amount": amount, "user_id": 4, "t": i * 1000})
        assert response.status_code == 200

    # User 2's two deposits
    for i, amount in enumerate(["15.00", "25.00"], 3):
        response = client.post("/event", json={"type": "deposit", "amount": amount, "user_id": 5, "t": i * 1000})
        assert response.status_code == 200
        assert not response.json()["alert"]

    # User 1's third deposit - should trigger alert
    response = client.post("/event", json={"type": "deposit", "amount": "30.00", "user_id": 4, "t": 5000})
    assert response.status_code == 200
    assert response.json()["alert"]
    assert AlertCode.ALERT_300.value in [code for code in response.json()["alert_codes"]]
