"""Event router handling transaction event processing and rule evaluation."""

import asyncio
from typing import Final

from fastapi import APIRouter, Depends, HTTPException, status

from app.models.event import EventRequest, EventResponse
from app.models.rules import (
    Rule30_ConsecutiveWithdrawalsRule,
    Rule123_WindowedDepositRule,
    Rule300_IncreasingDepositsRule,
    Rule1100_LargeWithdrawalRule,
)
from app.services.rule_manager import RuleManager
from app.services.state_manager import StateManager

router = APIRouter(prefix="/event", tags=["event"])

MAX_RETRIES: Final[int] = 5
RETRY_DELAY: Final[float] = 0.1  # seconds


@router.post("", response_model=EventResponse)
async def event(
    request: EventRequest,
    state_manager: StateManager = Depends(),
) -> EventResponse:
    """Process a transaction event and evaluate rules.

    Args:
        request: The event request containing transaction details
        state_manager: Dependency-injected state manager for handling event state

    Returns:
        EventResponse containing any triggered alert codes

    Raises:
        HTTPException: If unable to acquire lock or other errors occur
    """
    retries = 0
    while retries < MAX_RETRIES:
        try:
            # Try to acquire lock
            if state_manager.acquire_lock(request.user_id):
                try:
                    # Save event to state manager
                    state_manager.save_event(request)

                    # Initialize and configure rule manager
                    rule_manager = RuleManager()
                    # Register each rule
                    rule_manager.register_rules(
                        [
                            Rule1100_LargeWithdrawalRule(),
                            Rule30_ConsecutiveWithdrawalsRule(),
                            Rule300_IncreasingDepositsRule(),
                            Rule123_WindowedDepositRule(),
                        ]
                    )

                    # Evaluate rules
                    alert_codes = rule_manager.evaluate_rules(request, state_manager)

                    return EventResponse(alert_codes=alert_codes, user_id=request.user_id)

                except Exception as e:
                    # Log the error and return 500
                    # TODO: Add proper logging
                    print(f"Error processing event: {str(e)}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error processing event"
                    ) from e
                finally:
                    # Always release the lock, even if an error occurs
                    state_manager.release_lock(request.user_id)

            # If we couldn't acquire the lock, wait and retry
            retries += 1
            if retries < MAX_RETRIES:
                await asyncio.sleep(RETRY_DELAY)

        except Exception as e:
            # Log any unexpected errors
            # TODO: Add proper logging
            print(f"Unexpected error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected error occurred"
            ) from e

    # If we exhausted all retries
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Unable to process event. Please try again.",
    )
