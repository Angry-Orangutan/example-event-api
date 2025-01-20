from decimal import Decimal

import pytest

from app.models.event import EventRequest, EventType
from app.services.state_manager import StateManager
from tests.unit.services.state_manager.test_base import state_manager  # noqa: F401


@pytest.mark.usefixtures("state_manager")
def test_get_recent_user_events_basic(state_manager: StateManager):  # noqa: F811
    """Test getting last N events for a user with basic scenario."""
    events = [
        EventRequest(type=EventType.DEPOSIT, amount=Decimal("100"), user_id=1, t=100),
        EventRequest(type=EventType.WITHDRAW, amount=Decimal("50"), user_id=1, t=200),
        EventRequest(type=EventType.DEPOSIT, amount=Decimal("75"), user_id=1, t=300),
    ]

    for event in events:
        state_manager.save_event(event)

    last_2_events = state_manager.get_user_events(user_id=1, limit=2)
    assert len(last_2_events) == 2
    assert [e.t for e in last_2_events] == [300, 200]  # Most recent first


@pytest.mark.usefixtures("state_manager")
def test_get_recent_user_events_more_than_available(state_manager: StateManager):  # noqa: F811
    """Test requesting more events than available returns all events."""
    events = [
        EventRequest(type=EventType.DEPOSIT, amount=Decimal("100"), user_id=1, t=100),
        EventRequest(type=EventType.WITHDRAW, amount=Decimal("50"), user_id=1, t=200),
    ]

    for event in events:
        state_manager.save_event(event)

    # Request 5 events when only 2 exist
    all_events = state_manager.get_user_events(user_id=1, limit=5)
    assert len(all_events) == 2
    assert [e.t for e in all_events] == [200, 100]


@pytest.mark.usefixtures("state_manager")
def test_get_recent_user_events_multiple_users(state_manager: StateManager):  # noqa: F811
    """Test that events from different users don't interfere."""
    # Add events for user 1
    user1_events = [
        EventRequest(type=EventType.DEPOSIT, amount=Decimal("100"), user_id=1, t=100),
        EventRequest(type=EventType.WITHDRAW, amount=Decimal("50"), user_id=1, t=200),
    ]

    # Add events for user 2
    user2_events = [
        EventRequest(type=EventType.DEPOSIT, amount=Decimal("200"), user_id=2, t=150),
        EventRequest(type=EventType.DEPOSIT, amount=Decimal("300"), user_id=2, t=250),
    ]

    for event in user1_events + user2_events:
        state_manager.save_event(event)

    # Get last event for each user
    user1_last = state_manager.get_user_events(user_id=1, limit=1)
    user2_last = state_manager.get_user_events(user_id=2, limit=1)

    assert len(user1_last) == 1
    assert len(user2_last) == 1
    assert user1_last[0].t == 200
    assert user2_last[0].t == 250


@pytest.mark.usefixtures("state_manager")
def test_get_recent_user_events_empty(state_manager: StateManager):  # noqa: F811
    """Test getting events for user with no events."""
    events = state_manager.get_user_events(user_id=999, limit=5)
    assert len(events) == 0
