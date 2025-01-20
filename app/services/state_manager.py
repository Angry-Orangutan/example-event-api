"""State manager for handling event persistence and retrieval using Redis.

This module provides a singleton StateManager class that handles all event-related
state operations using Redis as the backing store. It implements locking mechanisms
for concurrent access and provides methods for event storage and retrieval.
"""

import json
import uuid
from decimal import Decimal
from typing import ClassVar, Final, List, Optional, cast

from fakeredis import FakeRedis

from app.models.event import EventModel, EventType


class StateManager:
    """Singleton class for managing event state and persistence.

    This class provides thread-safe access to event data using Redis as the backing store.
    It implements a distributed locking mechanism to handle concurrent access to user data.

    Attributes:
        _instance: Singleton instance of StateManager
        _redis: Redis client instance
        _lock_timeout: Lock timeout in seconds
    """

    _instance: Optional["StateManager"] = None
    _redis: Optional[FakeRedis] = None
    _DEFAULT_LOCK_TIMEOUT: Final[int] = 1
    _lock_timeout: ClassVar[int] = _DEFAULT_LOCK_TIMEOUT

    def __new__(cls) -> "StateManager":
        """Ensure singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize Redis connection if not already initialized."""
        if self._redis is None:
            self._redis = FakeRedis(decode_responses=True)

    @property
    def redis(self) -> FakeRedis:
        """Get the Redis instance, initializing it if needed.

        Returns:
            FakeRedis: The Redis client instance
        """
        if self._redis is None:
            self._redis = FakeRedis(decode_responses=True)
        return self._redis

    @classmethod
    def get_lock_timeout(cls) -> int:
        """Get the current lock timeout value.

        Returns:
            int: Lock timeout in seconds
        """
        return cls._lock_timeout

    @classmethod
    def set_lock_timeout(cls, timeout: int) -> None:
        """Set the lock timeout value.

        This method is primarily for testing purposes. In production,
        the default timeout should be used.

        Args:
            timeout: New lock timeout in seconds

        Raises:
            ValueError: If timeout is less than 1
        """
        if timeout < 1:
            raise ValueError("Lock timeout must be at least 1 second")
        cls._lock_timeout = timeout

    def acquire_lock(self, user_id: int) -> bool:
        """Acquire a distributed lock for a user using Redis.

        Args:
            user_id: The ID of the user to lock

        Returns:
            bool: True if lock was acquired, False otherwise

        Raises:
            RuntimeError: If Redis operation fails
        """
        try:
            lock_key = f"lock:user:{user_id}"
            # Use setnx (SET if Not eXists) for atomic lock acquisition
            # Also set an expiration to prevent deadlocks
            acquired = self.redis.set(lock_key, "1", nx=True, ex=self._lock_timeout)  # type: ignore
            return bool(acquired)
        except Exception as e:
            raise RuntimeError(f"Failed to acquire lock for user {user_id}") from e

    def release_lock(self, user_id: int) -> None:
        """Release the distributed lock for a user.

        Args:
            user_id: The ID of the user whose lock to release

        Raises:
            RuntimeError: If Redis operation fails
        """
        try:
            lock_key = f"lock:user:{user_id}"
            self.redis.delete(lock_key)  # type: ignore
        except Exception as e:
            raise RuntimeError(f"Failed to release lock for user {user_id}") from e

    def save_event(self, event: EventModel) -> None:
        """Save event data to Redis using both hash (for data) and sorted set (for ordering).

        Args:
            event: The event to save

        Raises:
            RuntimeError: If Redis operation fails
        """
        try:
            # Create unique event key using UUID
            event_id = str(uuid.uuid4())
            event_key = f"user:{event.user_id}:event:{event_id}"

            # Store full event data in a hash
            event_data = {"type": event.type, "amount": str(event.amount), "user_id": event.user_id, "t": event.t}
            self.redis.set(event_key, json.dumps(event_data))  # type: ignore

            # Add to sorted sets for efficient querying, using timestamp as score
            sorted_set_key = f"user:{event.user_id}:events_by_time:{event.type}"
            self.redis.zadd(sorted_set_key, {event_key: event.t})  # type: ignore
        except Exception as e:
            raise RuntimeError(f"Failed to save event for user {event.user_id}") from e

    def get_user_events(self, user_id: int, limit: int = 0) -> list[EventModel]:
        """Get last n events for a user ordered by timestamp descending.

        Args:
            user_id: The user ID to get events for
            limit: Maximum number of events to return (0 for no limit)

        Returns:
            list[EventModel]: List of events ordered by timestamp descending

        Raises:
            RuntimeError: If Redis operation fails
        """
        try:
            deposit_events = self.get_user_events_by_type(user_id, EventType.DEPOSIT, limit)
            withdraw_events = self.get_user_events_by_type(user_id, EventType.WITHDRAW, limit)

            events = sorted(deposit_events + withdraw_events, key=lambda x: x.t, reverse=True)
            if limit >= 1 and len(events) > limit:
                events = events[:limit]

            return events
        except Exception as e:
            raise RuntimeError(f"Failed to get events for user {user_id}") from e

    def get_user_events_by_type(self, user_id: int, event_type: EventType, limit: int = 0) -> list[EventModel]:
        """Get all events for a user filtered by event type.

        Args:
            user_id: The user ID to get events for
            event_type: Type of events to retrieve
            limit: Maximum number of events to return (0 for no limit)

        Returns:
            list[EventModel]: List of events of the specified type

        Raises:
            RuntimeError: If Redis operation fails
        """
        sorted_set_key = f"user:{user_id}:events_by_time:{event_type}"

        try:
            event_keys = cast(list[str], self.redis.zrange(sorted_set_key, start=0, end=limit - 1, desc=True))
            if not event_keys:
                return []
            return self._fetch_events_from_keys(event_keys)  # type: ignore

        except Exception as e:
            raise RuntimeError(f"Failed to get events by type for user {user_id}") from e

    def get_user_events_by_time_range(self, user_id: int, start_time: int, end_time: int) -> list[EventModel]:
        """Get all events for a user within a time window.

        Args:
            user_id: The user ID to get events for
            start_time: Start of time window (inclusive)
            end_time: End of time window (inclusive)

        Returns:
            list[EventModel]: List of events within the time window

        Raises:
            RuntimeError: If Redis operation fails
        """
        try:
            deposit_events = self.get_user_events_by_type_time_range(user_id, EventType.DEPOSIT, start_time, end_time)
            withdraw_events = self.get_user_events_by_type_time_range(user_id, EventType.WITHDRAW, start_time, end_time)
            return sorted(deposit_events + withdraw_events, key=lambda x: x.t, reverse=True)
        except Exception as e:
            raise RuntimeError(f"Failed to get events by time range for user {user_id}") from e

    def get_user_events_by_type_time_range(
        self, user_id: int, event_type: EventType, start_time: int = 0, end_time: int = -1
    ) -> list[EventModel]:
        """Get all events for a user within a time window, filtered by type.

        Args:
            user_id: The user ID to get events for
            event_type: Type of events to retrieve
            start_time: Start of time window (inclusive)
            end_time: End of time window (inclusive)

        Returns:
            list[EventModel]: List of events of the specified type within the time window

        Raises:
            RuntimeError: If Redis operation fails
        """
        sorted_set_key = f"user:{user_id}:events_by_time:{event_type}"

        try:
            # Get event keys within time range using zrange (+byscore)
            event_keys = cast(
                List[str],
                self.redis.zrange(sorted_set_key, start=start_time, end=end_time, byscore=True),
            )  # type: ignore
            if not event_keys:
                return []
            return self._fetch_events_from_keys(event_keys)

        except Exception as e:
            raise RuntimeError(f"Failed to get events by type and time range for user {user_id}") from e

    def _fetch_events_from_keys(self, event_keys: list[str]) -> list[EventModel]:
        """Internal method to fetch EventModel objects from Redis keys.

        Args:
            event_keys: List of Redis keys to fetch events from

        Returns:
            list[EventModel]: List of events

        Raises:
            RuntimeError: If Redis operation fails
        """
        events = []
        for key in event_keys:
            try:
                event_data_str = self.redis.get(key)  # type: ignore
                if event_data_str is None:
                    continue
                event_data = json.loads(str(event_data_str))
                events.append(
                    EventModel(
                        type=event_data["type"],
                        amount=Decimal(event_data["amount"]),
                        user_id=event_data["user_id"],
                        t=event_data["t"],
                    )
                )
            except Exception as e:
                # Log the error but continue processing other events
                # TODO: Add logging
                print(f"Error fetching event {key}: {str(e)}")
                continue
        return events

    def _get_all_user_events(self, user_id: int) -> list[EventModel]:
        """DEBUG ONLY: Get all events for a user."""
        events = []
        pattern = f"user:{user_id}:event:*"

        for key in self.redis.scan_iter(match=pattern):  # type: ignore
            event_data_str = cast(Optional[str], self.redis.get(key))  # type: ignore
            if event_data_str is None:
                continue
            event_data = json.loads(event_data_str)
            events.append(
                EventModel(
                    type=event_data["type"],
                    amount=Decimal(event_data["amount"]),
                    user_id=event_data["user_id"],
                    t=event_data["t"],
                )
            )

        return events

    def clear(self) -> None:
        """Clear all data - mainly for testing purposes.

        Raises:
            RuntimeError: If Redis operation fails
        """
        try:
            self.redis.flushall(asynchronous=False)  # type: ignore
        except Exception as e:
            raise RuntimeError("Failed to clear state") from e
