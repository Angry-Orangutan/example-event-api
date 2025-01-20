from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.models.event import EventRequest, EventType


def test_valid_event_types():
    # Test deposit type
    request = EventRequest(type=EventType.DEPOSIT, amount=Decimal("100"), user_id=1, t=123)
    assert request.type == EventType.DEPOSIT

    # Test withdraw type
    request = EventRequest(type=EventType.WITHDRAW, amount=Decimal("100"), user_id=1, t=123)
    assert request.type == EventType.WITHDRAW

    # Test invalid type
    with pytest.raises(ValidationError):
        EventRequest(type="invalid_type", amount=Decimal("100"), user_id=1, t=123)  # type: ignore


def test_required_parameters():
    # Missing type field
    with pytest.raises(ValidationError):
        EventRequest(amount=Decimal("100"), user_id=1, t=123)  # type: ignore

    # Missing amount field
    with pytest.raises(ValidationError):
        EventRequest(type=EventType.DEPOSIT, user_id=1, t=123)  # type: ignore

    # Missing user_id field
    with pytest.raises(ValidationError):
        EventRequest(type=EventType.DEPOSIT, amount=Decimal("100"), t=123)  # type: ignore

    # Missing t field
    with pytest.raises(ValidationError):
        EventRequest(type=EventType.DEPOSIT, amount=Decimal("100"), user_id=1)  # type: ignore


def test_amount_validation():
    # Test valid amounts
    request = EventRequest(type=EventType.DEPOSIT, amount=Decimal("0"), user_id=1, t=123)
    assert request.amount == Decimal("0")

    request = EventRequest(type=EventType.DEPOSIT, amount=Decimal("1000000"), user_id=1, t=123)
    assert request.amount == Decimal("1000000")

    # Test invalid amounts
    with pytest.raises(ValidationError):
        EventRequest(type=EventType.DEPOSIT, amount=Decimal("-1"), user_id=1, t=123)

    with pytest.raises(ValidationError):
        EventRequest(type=EventType.DEPOSIT, amount=Decimal("1000001"), user_id=1, t=123)


def test_timestamp_validation():
    # Test valid timestamps
    request = EventRequest(type=EventType.DEPOSIT, amount=Decimal("100"), user_id=1, t=0)
    assert request.t == 0

    request = EventRequest(type=EventType.DEPOSIT, amount=Decimal("100"), user_id=1, t=1000000)
    assert request.t == 1000000

    # Test invalid timestamps
    with pytest.raises(ValidationError):
        EventRequest(type=EventType.DEPOSIT, amount=Decimal("100"), user_id=1, t=-1)

    with pytest.raises(ValidationError):
        EventRequest(type=EventType.DEPOSIT, amount=Decimal("100"), user_id=1, t=1000001)
