from decimal import Decimal
from enum import Enum
from typing import List

from pydantic import BaseModel, Field, computed_field

from app.models.alert import AlertCode


class EventType(str, Enum):
    DEPOSIT = "deposit"
    WITHDRAW = "withdraw"


class EventModel(BaseModel):
    type: EventType
    amount: Decimal = Field(
        ge=Decimal("0"),
        le=Decimal("1000000"),
        description="Amount of the deposit or withdrawal. Should be between 0 and 1,000,000",
    )
    user_id: int
    t: int = Field(
        ge=0,
        le=1000000,
        description="Timestamp of the event. Should be between 0 and 1,000,000",
    )


class EventRequest(EventModel):
    pass


class EventResponse(BaseModel):
    alert_codes: List[AlertCode] = []
    user_id: int

    @computed_field  # type: ignore[misc]
    @property
    def alert(self) -> bool:
        return len(self.alert_codes) > 0
