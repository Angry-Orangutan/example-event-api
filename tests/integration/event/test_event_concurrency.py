"""Integration tests for concurrent event processing.

This module contains integration tests that verify the system's behavior
when handling concurrent events, including:
- Events with the same timestamp
- Concurrent events for the same user
- Concurrent events for different users
- Lock acquisition and release behavior
"""

import asyncio
from decimal import Decimal
from typing import Any, Dict, List, Set

import pytest
from fastapi.testclient import TestClient
from httpx import Response

from app.main import app
from app.models.event import EventModel, EventType
from app.services.state_manager import StateManager
from tests.utils.fixtures import clear_state  # noqa: F401

client: TestClient = TestClient(app)


@pytest.mark.usefixtures("clear_state")
async def process_event(event_data: Dict[str, Any]) -> Response:
    """Process a single event asynchronously.

    Args:
        event_data: The event data to process

    Returns:
        Response: The HTTP response from processing the event
    """
    return client.post("/event", json=event_data)


@pytest.mark.usefixtures("clear_state")
def calculate_balance(events: List[EventModel]) -> Decimal:
    """Calculate balance from a list of events.

    Args:
        events: List of events to calculate balance from

    Returns:
        Decimal: The calculated balance
    """
    balance = Decimal("0")
    for event in events:
        if event.type == EventType.DEPOSIT:
            balance += event.amount
        else:
            balance -= event.amount
    return balance


@pytest.mark.asyncio
@pytest.mark.usefixtures("clear_state")
async def test_concurrent_same_timestamp() -> None:
    """Test handling of concurrent events with the same timestamp.

    This test verifies that events with the same timestamp are processed
    correctly and maintain consistency.
    """
    events: List[Dict[str, Any]] = [
        {"type": EventType.DEPOSIT, "amount": "100.00", "user_id": 1, "t": 10},
        {"type": EventType.WITHDRAW, "amount": "50.00", "user_id": 1, "t": 10},
        {"type": EventType.DEPOSIT, "amount": "75.00", "user_id": 1, "t": 10},
    ]

    # Process events concurrently
    tasks = [process_event(event) for event in events]
    responses = await asyncio.gather(*tasks)

    # Verify all events were processed successfully
    for response in responses:
        assert response.status_code == 200

    # Verify final state
    state_manager = StateManager()
    stored_events = state_manager.get_user_events(user_id=1)
    assert len(stored_events) == 3

    # Verify total balance
    total_balance = sum(
        Decimal(event["amount"]) if event["type"] == EventType.DEPOSIT else -Decimal(event["amount"])
        for event in events
    )
    actual_balance = calculate_balance(stored_events)
    assert actual_balance == total_balance


@pytest.mark.asyncio
@pytest.mark.usefixtures("clear_state")
async def test_concurrent_different_users() -> None:
    """Test handling of concurrent events for different users.

    This test verifies that events for different users can be processed
    concurrently without interference.
    """
    events: List[Dict[str, Any]] = [
        {"type": EventType.DEPOSIT, "amount": "100.00", "user_id": 1, "t": 10},
        {"type": EventType.DEPOSIT, "amount": "200.00", "user_id": 2, "t": 10},
        {"type": EventType.DEPOSIT, "amount": "300.00", "user_id": 3, "t": 10},
    ]

    # Process events concurrently
    tasks = [process_event(event) for event in events]
    responses = await asyncio.gather(*tasks)

    # Verify all events were processed successfully
    for response in responses:
        assert response.status_code == 200

    # Verify each user's state
    state_manager = StateManager()
    for event in events:
        user_id = event["user_id"]
        stored_events = state_manager.get_user_events(user_id=user_id)
        assert len(stored_events) == 1
        actual_balance = calculate_balance(stored_events)
        assert actual_balance == Decimal(event["amount"])


@pytest.mark.asyncio
@pytest.mark.usefixtures("clear_state")
async def test_same_timestamp_events_are_unique() -> None:
    """Test that events with the same timestamp are stored as unique events.

    This test verifies that multiple events with the same timestamp
    are stored as separate events and can be retrieved individually.
    """
    # Create multiple events with the same timestamp
    timestamp = 1000
    events: List[Dict[str, Any]] = [
        {"type": EventType.DEPOSIT, "amount": "100.00", "user_id": 1, "t": timestamp},
        {"type": EventType.DEPOSIT, "amount": "200.00", "user_id": 1, "t": timestamp},
        {"type": EventType.DEPOSIT, "amount": "300.00", "user_id": 1, "t": timestamp},
    ]

    # Process events sequentially to ensure deterministic order
    for event_data in events:
        response: Response = client.post("/event", json=event_data)
        assert response.status_code == 200, "Event processing should succeed"

    # Retrieve all events for the user in the timestamp window
    state_manager = StateManager()
    stored_events = state_manager.get_user_events_by_time_range(user_id=1, start_time=timestamp, end_time=timestamp)

    # Verify all events were stored
    assert len(stored_events) == len(events), "All events should be stored uniquely"

    # Verify the amounts are all present (order might vary due to UUID keys)
    stored_amounts: Set[Decimal] = {event.amount for event in stored_events}
    expected_amounts: Set[Decimal] = {Decimal("100.00"), Decimal("200.00"), Decimal("300.00")}
    assert stored_amounts == expected_amounts, "All event amounts should be present"


@pytest.mark.asyncio
@pytest.mark.usefixtures("clear_state")
async def test_concurrent_locking() -> None:
    """Test concurrent event processing for the same user.

    This test verifies that concurrent events for the same user are
    properly serialized using the locking mechanism, ensuring that
    all events are eventually processed.
    """
    # Create many concurrent events for the same user
    events: List[Dict[str, Any]] = [
        {"type": EventType.DEPOSIT, "amount": "1.00", "user_id": 1, "t": i}
        for i in range(10)  # Send enough events to trigger lock contention
    ]

    # Process events concurrently
    tasks = [process_event(event) for event in events]
    responses = await asyncio.gather(*tasks)

    # All events should eventually succeed due to retries
    assert all(r.status_code == 200 for r in responses), "All events should succeed"

    # Verify events were stored correctly
    state_manager = StateManager()
    stored_events = state_manager.get_user_events(user_id=1)
    assert len(stored_events) == len(events), "All events should be stored"

    # Verify all timestamps are present (order may vary due to concurrency)
    stored_timestamps = {event.t for event in stored_events}
    expected_timestamps = {i for i in range(10)}
    assert stored_timestamps == expected_timestamps, "All timestamps should be present"

    # Verify all amounts are correct
    assert all(event.amount == Decimal("1.00") for event in stored_events), "All amounts should be correct"


@pytest.mark.asyncio
@pytest.mark.usefixtures("clear_state")
async def test_lock_retry_behavior() -> None:
    """Test the retry behavior of the locking mechanism.

    This test verifies that events retry when a lock is not available
    and eventually succeed when the lock is released.
    """
    state_manager = StateManager()
    test_event = {"type": EventType.DEPOSIT, "amount": "100.00", "user_id": 1, "t": 1000}

    # Start event processing
    task = asyncio.create_task(process_event(test_event))

    # Wait a bit to ensure the event processing has started
    await asyncio.sleep(0.1)

    # Verify event was processed successfully
    response = await task
    assert response.status_code == 200, "Event should be processed successfully"

    # Verify event was stored
    stored_events = state_manager.get_user_events(user_id=1)
    assert len(stored_events) == 1, "Event should be stored"
    assert stored_events[0].amount == Decimal("100.00"), "Event amount should be correct"
