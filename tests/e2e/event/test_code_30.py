import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.alert import AlertCode
from tests.utils.fixtures import clear_state  # noqa: F401

client = TestClient(app)


@pytest.mark.usefixtures("clear_state")
def test_three_consecutive_withdrawals_triggers_alert() -> None:
    """
    Test that three consecutive withdrawals trigger Alert 30.

    Scenario:
    1. Make first withdrawal
    2. Make second withdrawal
    3. Make third withdrawal
    4. Verify Alert 30 is triggered on the third withdrawal
    """
    user_id = 1

    # First withdrawal
    response = client.post("/event", json={"type": "withdraw", "amount": "1", "user_id": user_id, "t": 1000})
    assert response.status_code == 200
    assert not response.json()["alert"]

    # Second withdrawal
    response = client.post("/event", json={"type": "withdraw", "amount": "2", "user_id": user_id, "t": 2000})
    assert response.status_code == 200
    assert not response.json()["alert"]

    # Third withdrawal - should trigger alert
    response = client.post("/event", json={"type": "withdraw", "amount": "3", "user_id": user_id, "t": 3000})
    assert response.status_code == 200
    assert response.json()["alert"]
    assert AlertCode.ALERT_30.value in [code for code in response.json()["alert_codes"]]


@pytest.mark.usefixtures("clear_state")
def test_deposit_breaks_consecutive_withdrawals() -> None:
    """
    Test that a deposit between withdrawals prevents Alert 30 from triggering.

    Scenario:
    1. Make first withdrawal
    2. Make a deposit
    3. Make second withdrawal
    4. Make third withdrawal
    5. Verify Alert 30 is not triggered
    """
    user_id = 2

    # First withdrawal
    response = client.post("/event", json={"type": "withdraw", "amount": "50", "user_id": user_id, "t": 1000})
    assert response.status_code == 200

    # Deposit breaks the sequence
    response = client.post("/event", json={"type": "deposit", "amount": "100", "user_id": user_id, "t": 2000})
    assert response.status_code == 200

    # Second withdrawal
    response = client.post("/event", json={"type": "withdraw", "amount": "25", "user_id": user_id, "t": 3000})
    assert response.status_code == 200

    # Third withdrawal - should not trigger alert due to deposit
    response = client.post("/event", json={"type": "withdraw", "amount": "25", "user_id": user_id, "t": 4000})
    assert response.status_code == 200
    assert not response.json()["alert"]
    assert AlertCode.ALERT_30.value not in [code for code in response.json()["alert_codes"]]


@pytest.mark.usefixtures("clear_state")
def test_less_than_three_withdrawals_no_alert() -> None:
    """
    Test that less than three withdrawals do not trigger Alert 30.

    Scenario:
    1. Make first withdrawal
    2. Make second withdrawal
    3. Verify Alert 30 is not triggered
    """
    user_id = 3

    # First withdrawal
    response = client.post("/event", json={"type": "withdraw", "amount": "50", "user_id": user_id, "t": 1000})
    assert response.status_code == 200
    assert not response.json()["alert"]

    # Second withdrawal
    response = client.post("/event", json={"type": "withdraw", "amount": "75", "user_id": user_id, "t": 2000})
    assert response.status_code == 200
    assert not response.json()["alert"]


@pytest.mark.usefixtures("clear_state")
def test_multiple_alerts_can_trigger() -> None:
    """
    Test that Alert 30 can trigger alongside other alerts.

    Scenario:
    1. Make first withdrawal
    2. Make second withdrawal
    3. Make third large withdrawal (>100)
    4. Verify both Alert 30 and Alert 1100 are triggered
    """
    user_id = 4

    # First withdrawal
    response = client.post("/event", json={"type": "withdraw", "amount": "50", "user_id": user_id, "t": 1000})
    assert response.status_code == 200

    # Second withdrawal
    response = client.post("/event", json={"type": "withdraw", "amount": "75", "user_id": user_id, "t": 2000})
    assert response.status_code == 200

    # Third withdrawal - large amount to trigger both alerts
    response = client.post("/event", json={"type": "withdraw", "amount": "150", "user_id": user_id, "t": 3000})
    assert response.status_code == 200
    assert response.json()["alert"]
    alert_codes = response.json()["alert_codes"]
    assert AlertCode.ALERT_30.value in alert_codes
    assert AlertCode.ALERT_1100.value in alert_codes


@pytest.mark.usefixtures("clear_state")
def test_different_users_dont_interfere() -> None:
    """
    Test that withdrawals from different users don't interfere with each other's alerts.

    Scenario:
    1. User 1 makes two withdrawals
    2. User 2 makes two withdrawals
    3. User 1 makes third withdrawal
    4. Verify only User 1 triggers Alert 30
    """
    # User 1's first two withdrawals
    for t in [1000, 2000]:
        response = client.post("/event", json={"type": "withdraw", "amount": "50", "user_id": 5, "t": t})
        assert response.status_code == 200

    # User 2's two withdrawals
    for t in [3000, 4000]:
        response = client.post("/event", json={"type": "withdraw", "amount": "50", "user_id": 6, "t": t})
        assert response.status_code == 200
        assert not response.json()["alert"]

    # User 1's third withdrawal - should trigger alert
    response = client.post("/event", json={"type": "withdraw", "amount": "50", "user_id": 5, "t": 5000})
    assert response.status_code == 200
    assert response.json()["alert"]
    assert AlertCode.ALERT_30.value in [code for code in response.json()["alert_codes"]]
