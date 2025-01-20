"""Integration tests for the event endpoint.

This module contains integration tests for the event processing endpoint,
verifying that the API correctly handles different types of transactions
and validates requests.
"""

from decimal import Decimal
from typing import Any, Dict, List

import pytest
from fastapi.testclient import TestClient
from httpx import Response

from app.main import app
from app.models.alert import AlertCode
from app.models.event import EventType
from app.services.state_manager import StateManager
from tests.utils.fixtures import clear_state  # noqa: F401

client: TestClient = TestClient(app)


@pytest.mark.parametrize(
    "event_data,expected_alert,expected_alert_codes",
    [
        ({"type": EventType.DEPOSIT, "amount": "10.00", "user_id": 1, "t": 10}, False, []),
        ({"type": EventType.WITHDRAW, "amount": "10.00", "user_id": 1, "t": 10}, False, []),
        ({"type": EventType.DEPOSIT, "amount": "150.00", "user_id": 1, "t": 10}, False, []),
        ({"type": EventType.WITHDRAW, "amount": "150.00", "user_id": 1, "t": 10}, True, [AlertCode.ALERT_1100.value]),
        ({"type": EventType.WITHDRAW, "amount": "100.00", "user_id": 1, "t": 10}, False, []),
    ],
)
@pytest.mark.usefixtures("clear_state")
def test_valid_events(event_data: Dict[str, Any], expected_alert: bool, expected_alert_codes: List[int]) -> None:
    """Test processing of valid events.

    This test verifies that valid deposit and withdrawal events
    are processed correctly and return the expected response.

    Args:
        event_data: The event data to send
        expected_alert: Whether the event should trigger an alert
    """
    response: Response = client.post("/event", json=event_data)
    assert response.status_code == 200, "Event should be processed successfully"

    response_json = response.json()
    assert response_json["alert"] is expected_alert
    assert response_json["user_id"] == event_data["user_id"]
    assert sorted(response_json["alert_codes"]) == sorted(expected_alert_codes)


@pytest.mark.parametrize(
    "invalid_data,expected_status",
    [
        ({}, 422),  # Missing all fields
        ({"type": "invalid"}, 422),  # Invalid event type
        ({"type": EventType.DEPOSIT, "amount": "-1.00", "user_id": 1, "t": 0}, 422),  # Negative amount
        ({"type": EventType.DEPOSIT, "amount": "42.00", "user_id": -1, "t": 0}, 422),  # Negative user_id
        ({"type": EventType.DEPOSIT, "amount": "42.00", "user_id": 1, "t": -1}, 422),  # Negative timestamp
    ],
)
@pytest.mark.usefixtures("clear_state")
def test_invalid_events(invalid_data: Dict[str, Any], expected_status: int) -> None:
    """Test handling of invalid events.

    This test verifies that invalid events are rejected with appropriate
    error responses and status codes.

    Args:
        invalid_data: The invalid event data to send
        expected_status: Expected HTTP status code
    """
    response: Response = client.post("/event", json=invalid_data)
    assert response.status_code == expected_status

    if expected_status == 422:
        error_detail = response.json()["detail"]
        assert isinstance(error_detail, list), "Validation error should have details"
        assert len(error_detail) > 0, "Validation error should explain the issue"


@pytest.mark.usefixtures("clear_state")
def test_event_persistence() -> None:
    """Test that events are correctly persisted.

    This test verifies that processed events are correctly stored
    and can be retrieved from the state manager.
    """
    event_data = {
        "type": EventType.DEPOSIT,
        "amount": "42.00",
        "user_id": 1,
        "t": 10,
    }

    # Process the event
    response: Response = client.post("/event", json=event_data)
    assert response.status_code == 200

    # Verify event was stored
    state_manager = StateManager()
    stored_events = state_manager.get_user_events(user_id=1)
    assert len(stored_events) == 1

    stored_event = stored_events[0]
    assert stored_event.type == EventType.DEPOSIT
    assert stored_event.amount == Decimal("42.00")
    assert stored_event.user_id == 1
    assert stored_event.t == 10
