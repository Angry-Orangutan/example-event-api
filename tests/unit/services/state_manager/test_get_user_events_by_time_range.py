from decimal import Decimal

import pytest

from app.models.event import EventRequest, EventType
from app.services.state_manager import StateManager
from tests.unit.services.state_manager.test_base import state_manager  # noqa: F401


@pytest.mark.usefixtures("state_manager")
def test_get_user_events_by_time_range(state_manager: StateManager):  # noqa: F811
    """Test getting events within a specific time window."""
    # Create test events at different times
    events = [
        EventRequest(type=EventType.DEPOSIT, amount=Decimal("50"), user_id=1, t=100),
        EventRequest(type=EventType.WITHDRAW, amount=Decimal("30"), user_id=1, t=120),
        EventRequest(type=EventType.DEPOSIT, amount=Decimal("70"), user_id=1, t=140),
        EventRequest(type=EventType.DEPOSIT, amount=Decimal("90"), user_id=1, t=160),
    ]

    for event in events:
        state_manager.save_event(event)

    # Test getting all events in window
    window_events = state_manager.get_user_events_by_time_range(user_id=1, start_time=120, end_time=140)
    assert len(window_events) == 2
    assert window_events[0].t == 140
    assert window_events[1].t == 120

    # Test filtering by event type - deposits
    deposit_events = state_manager.get_user_events_by_type_time_range(
        user_id=1, start_time=100, end_time=160, event_type=EventType.DEPOSIT
    )
    assert len(deposit_events) == 3
    assert all(e.type == EventType.DEPOSIT for e in deposit_events)

    deposit_events_limited = state_manager.get_user_events_by_type_time_range(
        user_id=1, start_time=100, end_time=140, event_type=EventType.DEPOSIT
    )
    assert len(deposit_events_limited) == 2
    assert all(e.type == EventType.DEPOSIT for e in deposit_events_limited)

    # Test filtering by event type - withdrawals
    withdraw_events = state_manager.get_user_events_by_type_time_range(
        user_id=1, start_time=100, end_time=160, event_type=EventType.WITHDRAW
    )
    assert len(withdraw_events) == 1
    assert all(e.type == EventType.WITHDRAW for e in withdraw_events)

    withdraw_events_limited = state_manager.get_user_events_by_type_time_range(
        user_id=1, start_time=100, end_time=140, event_type=EventType.WITHDRAW
    )
    assert len(withdraw_events_limited) == 1
    assert all(e.type == EventType.WITHDRAW for e in withdraw_events_limited)

    # Test empty window
    empty_events = state_manager.get_user_events_by_time_range(user_id=1, start_time=0, end_time=50)
    assert len(empty_events) == 0

    # Test non-existent user
    other_user_events = state_manager.get_user_events_by_time_range(user_id=2, start_time=0, end_time=200)
    assert len(other_user_events) == 0
