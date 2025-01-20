from decimal import Decimal

import pytest

from app.models.event import EventRequest, EventType
from app.services.state_manager import StateManager
from tests.utils.fixtures import state_manager  # noqa: F401


@pytest.mark.usefixtures("state_manager")
def test_get_user_events_by_type_basic(state_manager: StateManager):  # noqa: F811
    """Test getting last N events of a specific type."""
    events = [
        EventRequest(type=EventType.DEPOSIT, amount=Decimal("100"), user_id=1, t=100),
        EventRequest(type=EventType.WITHDRAW, amount=Decimal("50"), user_id=1, t=200),
        EventRequest(type=EventType.DEPOSIT, amount=Decimal("75"), user_id=1, t=300),
        EventRequest(type=EventType.WITHDRAW, amount=Decimal("25"), user_id=1, t=400),
    ]

    for event in events:
        state_manager.save_event(event)

    # Get last 2 deposits
    deposits = state_manager.get_user_events_by_type(user_id=1, event_type=EventType.DEPOSIT, limit=2)
    assert len(deposits) == 2
    assert [e.t for e in deposits] == [300, 100]  # Most recent first
    assert all(e.type == EventType.DEPOSIT for e in deposits)

    # Get last 2 withdrawals
    withdrawals = state_manager.get_user_events_by_type(user_id=1, event_type=EventType.WITHDRAW, limit=2)
    assert len(withdrawals) == 2
    assert [e.t for e in withdrawals] == [400, 200]  # Most recent first
    assert all(e.type == EventType.WITHDRAW for e in withdrawals)


@pytest.mark.usefixtures("state_manager")
def test_get_user_events_by_type_sparse_events(state_manager: StateManager):  # noqa: F811
    """Test getting events of a specific type when they are sparse."""
    events = [
        EventRequest(type=EventType.WITHDRAW, amount=Decimal("50"), user_id=1, t=100),
        EventRequest(type=EventType.WITHDRAW, amount=Decimal("50"), user_id=1, t=200),
        EventRequest(type=EventType.DEPOSIT, amount=Decimal("100"), user_id=1, t=300),
        EventRequest(type=EventType.WITHDRAW, amount=Decimal("50"), user_id=1, t=400),
        EventRequest(type=EventType.WITHDRAW, amount=Decimal("50"), user_id=1, t=500),
        EventRequest(type=EventType.DEPOSIT, amount=Decimal("100"), user_id=1, t=600),
    ]

    for event in events:
        state_manager.save_event(event)

    # Get all deposits (they are sparse)
    deposits = state_manager.get_user_events_by_type(user_id=1, event_type=EventType.DEPOSIT, limit=2)
    assert len(deposits) == 2
    assert [e.t for e in deposits] == [600, 300]  # Most recent first
    assert all(e.type == EventType.DEPOSIT for e in deposits)


@pytest.mark.usefixtures("state_manager")
def test_get_user_events_by_type_multiple_users(state_manager: StateManager):  # noqa: F811
    """Test that events from different users don't interfere when filtering by type."""
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

    # Get deposits for each user
    user1_deposits = state_manager.get_user_events_by_type(user_id=1, event_type=EventType.DEPOSIT, limit=2)
    user2_deposits = state_manager.get_user_events_by_type(user_id=2, event_type=EventType.DEPOSIT, limit=2)

    assert len(user1_deposits) == 1
    assert len(user2_deposits) == 2
    assert user1_deposits[0].t == 100
    assert [e.t for e in user2_deposits] == [250, 150]


@pytest.mark.usefixtures("state_manager")
def test_get_recent_user_deposits(state_manager: StateManager):  # noqa: F811
    """Test the convenience method for getting recent deposits."""
    events = [
        EventRequest(type=EventType.WITHDRAW, amount=Decimal("50"), user_id=1, t=100),
        EventRequest(type=EventType.DEPOSIT, amount=Decimal("100"), user_id=1, t=200),
        EventRequest(type=EventType.WITHDRAW, amount=Decimal("25"), user_id=1, t=300),
        EventRequest(type=EventType.DEPOSIT, amount=Decimal("75"), user_id=1, t=400),
    ]

    for event in events:
        state_manager.save_event(event)

    deposits = state_manager.get_user_events_by_type(user_id=1, event_type=EventType.DEPOSIT, limit=2)
    assert len(deposits) == 2
    assert [e.t for e in deposits] == [400, 200]  # Most recent first
    assert all(e.type == EventType.DEPOSIT for e in deposits)


@pytest.mark.usefixtures("state_manager")
def test_get_recent_user_withdrawals(state_manager: StateManager):  # noqa: F811
    """Test the convenience method for getting recent withdrawals."""
    events = [
        EventRequest(type=EventType.DEPOSIT, amount=Decimal("100"), user_id=1, t=100),
        EventRequest(type=EventType.WITHDRAW, amount=Decimal("50"), user_id=1, t=200),
        EventRequest(type=EventType.DEPOSIT, amount=Decimal("75"), user_id=1, t=300),
        EventRequest(type=EventType.WITHDRAW, amount=Decimal("25"), user_id=1, t=400),
    ]

    for event in events:
        state_manager.save_event(event)

    withdrawals = state_manager.get_user_events_by_type(user_id=1, event_type=EventType.WITHDRAW, limit=2)
    assert len(withdrawals) == 2
    assert [e.t for e in withdrawals] == [400, 200]  # Most recent first
    assert all(e.type == EventType.WITHDRAW for e in withdrawals)


@pytest.mark.usefixtures("state_manager")
def test_get_recent_user_withdrawals_with_no_events(state_manager: StateManager):  # noqa: F811
    """Test getting recent withdrawals when there are no events."""
    events = state_manager.get_user_events_by_type(user_id=1, event_type=EventType.WITHDRAW, limit=3)
    assert len(events) == 0
