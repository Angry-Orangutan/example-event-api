"""Unit tests for the EventRequest model.

This module contains tests for validating the EventRequest model's
behavior, including field validation, type checking, and constraints.
"""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.models.event import MAX_AMOUNT, MAX_TIMESTAMP, MIN_AMOUNT, MIN_TIMESTAMP, EventRequest, EventType


@pytest.mark.parametrize(
    "event_type,expected",
    [
        (EventType.DEPOSIT, EventType.DEPOSIT),
        (EventType.WITHDRAW, EventType.WITHDRAW),
    ],
)
def test_valid_event_types(event_type: EventType, expected: EventType) -> None:
    """Test that valid event types are accepted.

    Args:
        event_type: The event type to test
        expected: The expected event type after validation
    """
    request = EventRequest(type=event_type, amount=Decimal("100"), user_id=1, t=123)
    assert request.type == expected


def test_invalid_event_type() -> None:
    """Test that invalid event types are rejected."""
    with pytest.raises(ValidationError):
        EventRequest(type="invalid_type", amount=Decimal("100"), user_id=1, t=123)  # type: ignore


@pytest.mark.parametrize(
    "missing_field",
    [
        {"amount": Decimal("100"), "user_id": 1, "t": 123},  # Missing type
        {"type": EventType.DEPOSIT, "user_id": 1, "t": 123},  # Missing amount
        {"type": EventType.DEPOSIT, "amount": Decimal("100"), "t": 123},  # Missing user_id
        {"type": EventType.DEPOSIT, "amount": Decimal("100"), "user_id": 1},  # Missing t
    ],
)
def test_required_parameters(missing_field: dict) -> None:
    """Test that all required fields must be present.

    Args:
        missing_field: Dictionary of fields with one required field missing
    """
    with pytest.raises(ValidationError):
        EventRequest(**missing_field)  # type: ignore


@pytest.mark.parametrize(
    "amount",
    [
        MIN_AMOUNT,  # Test minimum allowed amount
        Decimal("42.42"),  # Test typical amount
        MAX_AMOUNT,  # Test maximum allowed amount
    ],
)
def test_valid_amounts(amount: Decimal) -> None:
    """Test that valid amounts are accepted.

    Args:
        amount: The amount to test
    """
    request = EventRequest(type=EventType.DEPOSIT, amount=amount, user_id=1, t=123)
    assert request.amount == amount


@pytest.mark.parametrize(
    "amount",
    [
        Decimal("-0.01"),  # Test negative amount
        MAX_AMOUNT + Decimal("0.01"),  # Test amount over maximum
    ],
)
def test_invalid_amounts(amount: Decimal) -> None:
    """Test that invalid amounts are rejected.

    Args:
        amount: The invalid amount to test
    """
    with pytest.raises(ValidationError):
        EventRequest(type=EventType.DEPOSIT, amount=amount, user_id=1, t=123)


@pytest.mark.parametrize(
    "timestamp",
    [
        MIN_TIMESTAMP,  # Test minimum allowed timestamp
        42,  # Test typical timestamp
        MAX_TIMESTAMP,  # Test maximum allowed timestamp
    ],
)
def test_valid_timestamps(timestamp: int) -> None:
    """Test that valid timestamps are accepted.

    Args:
        timestamp: The timestamp to test
    """
    request = EventRequest(type=EventType.DEPOSIT, amount=Decimal("100"), user_id=1, t=timestamp)
    assert request.t == timestamp


@pytest.mark.parametrize(
    "timestamp",
    [
        -1,  # Test negative timestamp
        MAX_TIMESTAMP + 1,  # Test timestamp over maximum
    ],
)
def test_invalid_timestamps(timestamp: int) -> None:
    """Test that invalid timestamps are rejected.

    Args:
        timestamp: The invalid timestamp to test
    """
    with pytest.raises(ValidationError):
        EventRequest(type=EventType.DEPOSIT, amount=Decimal("100"), user_id=1, t=timestamp)
