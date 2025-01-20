from decimal import Decimal

import pytest

from app.models.alert import AlertCode
from app.models.event import EventRequest as Event
from app.models.event import EventType
from app.models.rule import RuleContext
from app.models.rules import Rule123_WindowedDepositRule
from app.services.state_manager import StateManager
from tests.utils.fixtures import state_manager  # noqa: F401


@pytest.mark.usefixtures("state_manager")
def test_micro_transactions_alert_123(state_manager: StateManager) -> None:  # noqa: F811
    """Test that Rule 123 correctly handles multiple micro transactions.

    Should trigger alert only when cumulative amount exceeds 200.
    Using 0.01 transactions until reaching 200.02 total.
    """
    rule = Rule123_WindowedDepositRule()
    base_time = 1000  # arbitrary start time
    user_id = 1  # Test user ID
    micro_amount = Decimal("0.1")
    transaction_batch_size = 1998

    # Add 1998 transactions to StateManager
    for i in range(transaction_batch_size):
        # Create and save current event
        current_event = Event(user_id=user_id, t=base_time, type=EventType.DEPOSIT, amount=micro_amount)

        # Save event to state manager
        state_manager.save_event(current_event)

    # The next two transactions should not trigger the alert
    for i in range(2):
        # Create and save current event
        current_event = Event(user_id=user_id, t=base_time, type=EventType.DEPOSIT, amount=micro_amount)

        # Save event to state manager
        state_manager.save_event(current_event)

        # Evaluate rule
        context = RuleContext(event=current_event, state_manager=state_manager)
        result = rule.evaluate(context)
        assert len(result) == 0, "Alert should not trigger until above 200.00"

    # The next two transactions should trigger the alert
    for i in range(2):
        # Create and save current event
        current_event = Event(user_id=user_id, t=base_time, type=EventType.DEPOSIT, amount=micro_amount)

        # Save event to state manager
        state_manager.save_event(current_event)

        # Evaluate rule
        context = RuleContext(event=current_event, state_manager=state_manager)
        result = rule.evaluate(context)

        assert AlertCode.ALERT_123 in result, "Alert should trigger above 200.00"
