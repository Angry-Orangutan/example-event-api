from decimal import Decimal

import pytest

from app.models.event import EventRequest, EventType
from app.services.state_manager import StateManager
from tests.utils.fixtures import state_manager  # noqa: F401


@pytest.mark.usefixtures("state_manager")
def test_save_and_retrieve_event(state_manager: StateManager):  # noqa: F811
    """Test saving and retrieving a single event."""
    event = EventRequest(type=EventType.DEPOSIT, amount=Decimal("100.50"), user_id=1, t=100)

    state_manager.save_event(event)

    events = state_manager._get_all_user_events(user_id=1)
    assert len(events) == 1
    assert events[0].type == event.type
    assert events[0].amount == event.amount
    assert events[0].user_id == event.user_id
    assert events[0].t == event.t
