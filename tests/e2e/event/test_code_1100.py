import pytest
from fastapi.testclient import TestClient
from httpx import Response

from app.main import app
from app.models.alert import AlertCode
from tests.utils.fixtures import clear_state  # noqa: F401

client = TestClient(app)


@pytest.mark.usefixtures("clear_state")
def test_withdrawal_over_100() -> None:
    """Test that withdrawal over 100 triggers alert code 1100"""
    response: Response = client.post(
        "/event",
        json={"type": "withdraw", "amount": "150.00", "user_id": 1, "t": 10},
    )
    assert response.status_code == 200
    response_json = response.json()
    assert response_json["alert"] is True
    assert response_json["user_id"] == 1
    assert response_json["alert_codes"] == [AlertCode.ALERT_1100.value]


@pytest.mark.usefixtures("clear_state")
def test_withdrawal_under_100() -> None:
    """Test that withdrawal under 100 doesn't trigger any alerts"""
    response: Response = client.post(
        "/event",
        json={"type": "withdraw", "amount": "99.00", "user_id": 1, "t": 10},
    )
    assert response.status_code == 200
    response_json = response.json()
    assert response_json["alert"] is False
    assert response_json["user_id"] == 1
    assert response_json["alert_codes"] == []


@pytest.mark.usefixtures("clear_state")
def test_withdrawal_of_100() -> None:
    """Test that withdrawal of 100 doesn't trigger alert code 1100"""
    response: Response = client.post(
        "/event",
        json={"type": "withdraw", "amount": "100.00", "user_id": 1, "t": 10},
    )
    assert response.status_code == 200
    response_json = response.json()
    assert response_json["alert"] is False
    assert response_json["user_id"] == 1
    assert response_json["alert_codes"] == []


@pytest.mark.usefixtures("clear_state")
def test_deposit_over_100() -> None:
    """Test that deposit over 100 doesn't trigger alert code 1100"""
    response: Response = client.post(
        "/event",
        json={"type": "deposit", "amount": "150.00", "user_id": 1, "t": 10},
    )
    assert response.status_code == 200
    response_json = response.json()
    assert response_json["alert"] is False
    assert response_json["user_id"] == 1
    assert response_json["alert_codes"] == []
