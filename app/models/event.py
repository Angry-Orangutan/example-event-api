"""Event models for transaction processing.

This module defines the data models for transaction events, including
request and response models. Pydantic is used for data validation and
serialization.
"""

import sys
from decimal import Decimal
from enum import Enum
from typing import Final, List

from pydantic import BaseModel, Field, computed_field

from app.models.alert import AlertCode

# Event validation constants
# TODO: Move to config (e.g. pydantic settings
MIN_AMOUNT: Final[Decimal] = Decimal("0")
MAX_AMOUNT: Final[Decimal] = Decimal("1000000")
MIN_TIMESTAMP: Final[int] = 0
MAX_TIMESTAMP: Final[int] = sys.maxsize


class EventType(str, Enum):
    """Type of transaction event.

    Attributes:
        DEPOSIT: Money being added to account
        WITHDRAW: Money being removed from account
    """

    DEPOSIT = "deposit"
    WITHDRAW = "withdraw"


class EventModel(BaseModel):
    """Base model for transaction events.

    This model defines the common fields for all transaction events
    and includes validation rules for amounts and timestamps.

    Attributes:
        type: Type of transaction (deposit/withdraw)
        amount: Transaction amount between 0 and 1,000,000
        user_id: ID of the user making the transaction
        t: Timestamp of the transaction
    """

    type: EventType
    amount: Decimal = Field(
        ge=MIN_AMOUNT,
        le=MAX_AMOUNT,
        description="Amount of the deposit or withdrawal. Should be between 0 and 1,000,000",
    )
    user_id: int = Field(gt=0, description="ID of the user making the transaction. Must be positive.")
    t: int = Field(
        ge=MIN_TIMESTAMP,
        le=MAX_TIMESTAMP,
        description="Timestamp of the event. Should be between 0 and [system max int value]",
    )


class EventRequest(EventModel):
    """Request model for transaction events.

    This model is used for incoming transaction requests.
    It inherits all fields and validation from EventModel.
    It's common to have fields in the request that are unrelated to the
    core model, so this serves as a placeholder for now...
    """

    pass


class EventResponse(BaseModel):
    """Response model for transaction events.

    This model is used for outgoing transaction responses.
    It includes any alert codes that were triggered by the transaction.

    Attributes:
        alert_codes: List of alert codes triggered by the transaction
        user_id: ID of the user who made the transaction
        alert: Computed field indicating if any alerts were triggered
    """

    alert_codes: List[AlertCode] = Field(
        default_factory=list, description="List of alert codes triggered by the transaction"
    )
    user_id: int = Field(gt=0, description="ID of the user who made the transaction")

    @computed_field  # type: ignore[misc]
    @property
    def alert(self) -> bool:
        """Indicates if any alerts were triggered.

        Returns:
            bool: True if any alert codes are present, False otherwise
        """
        return len(self.alert_codes) > 0
