import json
from decimal import Decimal
from typing import List, Optional, cast

from fakeredis import FakeRedis

from app.models.event import EventModel, EventType


class StateManager:
    _instance: Optional["StateManager"] = None
    _redis: FakeRedis

    def __new__(cls) -> "StateManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._redis = FakeRedis(decode_responses=True)
        return cls._instance

    def save_event(self, event: EventModel) -> None:
        """Save event data to Redis using both hash (for data) and sorted set (for ordering)."""
        # Create unique event key
        event_key = f"user:{event.user_id}:event:{event.type}:{event.t}"

        # Store full event data in a hash
        event_data = {"type": event.type, "amount": str(event.amount), "user_id": event.user_id, "t": event.t}
        self._redis.set(event_key, json.dumps(event_data))  # type: ignore

        # Add to sorted sets for efficient querying, using timestamp as score
        sorted_set_key = f"user:{event.user_id}:events_by_time:{event.type}"
        self._redis.zadd(sorted_set_key, {event_key: event.t})  # type: ignore

    def get_user_events(self, user_id: int, limit: int = 0) -> list[EventModel]:
        """Get last n events for a user ordered by timestamp descending efficiently using sorted sets."""
        deposit_events = self.get_user_events_by_type(user_id, EventType.DEPOSIT, limit)
        withdraw_events = self.get_user_events_by_type(user_id, EventType.WITHDRAW, limit)

        events = sorted(deposit_events + withdraw_events, key=lambda x: x.t, reverse=True)
        if limit >= 1 and len(events) > limit:
            events = events[:limit]

        return events

    def get_user_events_by_type(self, user_id: int, event_type: EventType, limit: int = 0) -> list[EventModel]:
        """Get all events for a user filtered by event type."""
        sorted_set_key = f"user:{user_id}:events_by_time:{event_type}"

        try:
            event_keys = cast(list[str], self._redis.zrange(sorted_set_key, start=0, end=limit - 1, desc=True))
            if not event_keys:
                return []
            return self._fetch_events_from_keys(event_keys)  # type: ignore

        except Exception as err:
            print(err)
            return []

    def get_user_events_by_time_range(self, user_id: int, start_time: int, end_time: int) -> list[EventModel]:
        """Get all events for a user within a time window, ordered by timestamp ascending."""
        deposit_events = self.get_user_events_by_type_time_range(user_id, EventType.DEPOSIT, start_time, end_time)
        withdraw_events = self.get_user_events_by_type_time_range(user_id, EventType.WITHDRAW, start_time, end_time)
        return sorted(deposit_events + withdraw_events, key=lambda x: x.t, reverse=True)

    def get_user_events_by_type_time_range(
        self, user_id: int, event_type: EventType, start_time: int = 0, end_time: int = -1
    ) -> list[EventModel]:
        """Get all events for a user within a time window, ordered by timestamp ascending."""
        sorted_set_key = f"user:{user_id}:events_by_time:{event_type}"

        try:
            # Get event keys within time range using zrange (+byscore)
            event_keys = cast(
                List[str],
                self._redis.zrange(sorted_set_key, start=start_time, end=end_time, byscore=True),
            )  # type: ignore
            if not event_keys:
                return []
            return self._fetch_events_from_keys(event_keys)

        except Exception as err:
            print(err)
            return []

    def _fetch_events_from_keys(self, event_keys: list[str]) -> list[EventModel]:
        """Internal method to fetch EventModel objects from Redis keys."""
        events = []
        for key in event_keys:
            try:
                event_data = json.loads(self._redis.get(key))  # type: ignore
                events.append(
                    EventModel(
                        type=event_data["type"],
                        amount=Decimal(event_data["amount"]),
                        user_id=event_data["user_id"],
                        t=event_data["t"],
                    )
                )
            except Exception as err:
                print(err)
                continue
        return events

    def _get_all_user_events(self, user_id: int) -> list[EventModel]:
        """DEBUG ONLY: Get all events for a user."""
        events = []
        pattern = f"user:{user_id}:event:*"

        for key in self._redis.scan_iter(match=pattern):  # type: ignore
            event_data = json.loads(self._redis.get(key))  # type: ignore
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
        """Clear all data - mainly for testing purposes."""
        self._redis.flushall(asynchronous=False)  # type: ignore
