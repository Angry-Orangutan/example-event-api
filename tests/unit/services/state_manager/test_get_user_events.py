from decimal import Decimal

import pytest

from app.models.event import EventRequest, EventType
from app.services.state_manager import StateManager
from tests.utils.fixtures import state_manager  # noqa: F401


@pytest.mark.usefixtures("state_manager")
def test_get_user_events(state_manager: StateManager):  # noqa: F811
    """Test retrieving events within a specific time range."""
    events = [
        EventRequest(type=EventType.DEPOSIT, amount=Decimal("100"), user_id=1, t=100),
        EventRequest(type=EventType.WITHDRAW, amount=Decimal("50"), user_id=1, t=200),
        EventRequest(type=EventType.DEPOSIT, amount=Decimal("75"), user_id=1, t=300),
    ]

    for event in events:
        state_manager.save_event(event)

    # Test getting all events
    all_events = state_manager.get_user_events(user_id=1)
    assert len(all_events) == 3
    assert [e.t for e in all_events] == [300, 200, 100]  # Check they're ordered by time


@pytest.mark.usefixtures("state_manager")
def test_get_user_events_multiple_users(state_manager: StateManager):  # noqa: F811
    """Test handling events for multiple users."""
    events = [
        EventRequest(type=EventType.DEPOSIT, amount=Decimal("100"), user_id=1, t=100),
        EventRequest(type=EventType.DEPOSIT, amount=Decimal("200"), user_id=2, t=100),
        EventRequest(type=EventType.WITHDRAW, amount=Decimal("50"), user_id=1, t=200),
    ]

    for event in events:
        state_manager.save_event(event)

    user1_events = state_manager.get_user_events(user_id=1)
    assert len(user1_events) == 2
    assert user1_events[0].amount == Decimal("50")
    assert user1_events[1].amount == Decimal("100")

    user2_events = state_manager.get_user_events(user_id=2)
    assert len(user2_events) == 1
    assert user2_events[0].amount == Decimal("200")
