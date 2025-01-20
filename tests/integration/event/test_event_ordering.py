"""Integration tests for event ordering.

This module contains tests that verify events submitted out of chronological order
are still processed and retrieved correctly by the system.
"""

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.event import EventType
from app.services.state_manager import StateManager
from tests.utils.fixtures import clear_state  # noqa: F401

client = TestClient(app)


@pytest.mark.usefixtures("clear_state")
def test_out_of_order_events() -> None:
    """Test that events submitted out of chronological order are processed correctly.

    This test simulates a LIFO (Last In First Out) queue in the frontend by submitting
    events in reverse chronological order, then verifies they are stored and retrieved
    in the correct chronological order.
    """
    user_id = 1
    events = [
        # Events in reverse chronological order (newest first)
        {"type": EventType.DEPOSIT, "amount": "30.00", "user_id": user_id, "t": 3000},
        {"type": EventType.DEPOSIT, "amount": "20.00", "user_id": user_id, "t": 2000},
        {"type": EventType.DEPOSIT, "amount": "10.00", "user_id": user_id, "t": 1000},
    ]

    # Submit events in reverse order (simulating LIFO queue)
    for event in events:
        response = client.post("/event", json=event)
        assert response.status_code == 200

    # Verify events are stored and can be retrieved in correct order
    state_manager = StateManager()
    stored_events = state_manager.get_user_events(user_id=user_id)

    # Events should be returned in reverse chronological order (newest first)
    assert len(stored_events) == 3
    assert [event.t for event in stored_events] == [3000, 2000, 1000]
    assert [event.amount for event in stored_events] == [
        Decimal("30.00"),
        Decimal("20.00"),
        Decimal("10.00"),
    ]


@pytest.mark.usefixtures("clear_state")
def test_mixed_order_events() -> None:
    """Test that events submitted in mixed order are processed correctly.

    This test submits events in a random order and verifies they are stored
    and retrieved in the correct chronological order.
    """
    user_id = 1
    events = [
        # Events in mixed order
        {"type": EventType.DEPOSIT, "amount": "20.00", "user_id": user_id, "t": 2000},
        {"type": EventType.DEPOSIT, "amount": "40.00", "user_id": user_id, "t": 4000},
        {"type": EventType.DEPOSIT, "amount": "10.00", "user_id": user_id, "t": 1000},
        {"type": EventType.DEPOSIT, "amount": "30.00", "user_id": user_id, "t": 3000},
    ]

    # Submit events in mixed order
    for event in events:
        response = client.post("/event", json=event)
        assert response.status_code == 200

    # Verify events are stored and can be retrieved in correct order
    state_manager = StateManager()
    stored_events = state_manager.get_user_events(user_id=user_id)

    # Events should be returned in reverse chronological order (newest first)
    assert len(stored_events) == 4
    assert [event.t for event in stored_events] == [4000, 3000, 2000, 1000]
    assert [event.amount for event in stored_events] == [
        Decimal("40.00"),
        Decimal("30.00"),
        Decimal("20.00"),
        Decimal("10.00"),
    ]


@pytest.mark.usefixtures("clear_state")
def test_out_of_order_mixed_event_types() -> None:
    """Test that different types of events submitted out of order are processed correctly.

    This test submits both deposits and withdrawals in mixed chronological order
    and verifies they are stored and retrieved in the correct order.
    """
    user_id = 1
    events = [
        # Events in mixed order with different types
        {"type": EventType.WITHDRAW, "amount": "20.00", "user_id": user_id, "t": 2000},
        {"type": EventType.DEPOSIT, "amount": "40.00", "user_id": user_id, "t": 4000},
        {"type": EventType.WITHDRAW, "amount": "10.00", "user_id": user_id, "t": 1000},
        {"type": EventType.DEPOSIT, "amount": "30.00", "user_id": user_id, "t": 3000},
    ]

    # Submit events in mixed order
    for event in events:
        response = client.post("/event", json=event)
        assert response.status_code == 200

    # Verify events are stored and can be retrieved in correct order
    state_manager = StateManager()
    stored_events = state_manager.get_user_events(user_id=user_id)

    # Events should be returned in reverse chronological order (newest first)
    assert len(stored_events) == 4
    assert [event.t for event in stored_events] == [4000, 3000, 2000, 1000]
    assert [event.amount for event in stored_events] == [
        Decimal("40.00"),
        Decimal("30.00"),
        Decimal("20.00"),
        Decimal("10.00"),
    ]
    assert [event.type for event in stored_events] == [
        EventType.DEPOSIT,
        EventType.DEPOSIT,
        EventType.WITHDRAW,
        EventType.WITHDRAW,
    ]
