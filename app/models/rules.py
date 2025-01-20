"""Rule implementations.

This module contains concrete implementations of rules.
Each rule class implements the Rule interface and defines specific logic
for detecting suspicious transaction patterns.
"""

from decimal import Decimal
from typing import Final, List

from app.models.alert import AlertCode
from app.models.event import EventType
from app.models.rule import Rule, RuleContext

# Rule-specific constants
# TODO: These should sit somewhere else, with more structure, coupled to their respective rules
LARGE_WITHDRAWAL_THRESHOLD: Final[Decimal] = Decimal("100")
CONSECUTIVE_WITHDRAWALS_COUNT: Final[int] = 3
INCREASING_DEPOSITS_COUNT: Final[int] = 3
WINDOWED_DEPOSITS_THRESHOLD: Final[Decimal] = Decimal("200")
WINDOWED_DEPOSITS_WINDOW: Final[int] = 30  # seconds


class Rule1100_LargeWithdrawalRule(Rule):
    """Rule 1100: Alert when withdrawal amount exceeds threshold.

    This rule checks if a single withdrawal transaction exceeds
    the large withdrawal threshold (currently £100).
    """

    def evaluate(self, context: RuleContext) -> List[AlertCode]:
        """Evaluate if the withdrawal amount exceeds the threshold.

        Args:
            context: RuleContext containing the event to evaluate

        Returns:
            List containing ALERT_1100 if threshold exceeded, empty list otherwise
        """
        if context.event.type == EventType.WITHDRAW and context.event.amount > LARGE_WITHDRAWAL_THRESHOLD:
            return [AlertCode.ALERT_1100]
        return []


class Rule30_ConsecutiveWithdrawalsRule(Rule):
    """Rule 30: Alert on consecutive withdrawals.

    This rule checks if there have been three consecutive withdrawal
    transactions, including the current event.
    """

    def evaluate(self, context: RuleContext) -> List[AlertCode]:
        """Evaluate if there are enough consecutive withdrawals.

        Args:
            context: RuleContext containing the event to evaluate

        Returns:
            List containing ALERT_30 if pattern detected, empty list otherwise
        """
        recent_events = context.state_manager.get_user_events(
            context.event.user_id, limit=CONSECUTIVE_WITHDRAWALS_COUNT
        )
        if len(recent_events) == CONSECUTIVE_WITHDRAWALS_COUNT and all(
            event.type == EventType.WITHDRAW for event in recent_events
        ):
            return [AlertCode.ALERT_30]
        return []


class Rule300_IncreasingDepositsRule(Rule):
    """Rule 300: Alert on consecutive increasing deposits.

    This rule checks if there have been three consecutive deposits
    with increasing amounts, ordered by timestamp descending.
    """

    def evaluate(self, context: RuleContext) -> List[AlertCode]:
        """Evaluate if there is an increasing deposits pattern.

        Args:
            context: RuleContext containing the event to evaluate

        Returns:
            List containing ALERT_300 if pattern detected, empty list otherwise
        """
        recent_deposits = context.state_manager.get_user_events_by_type(
            user_id=context.event.user_id, event_type=EventType.DEPOSIT, limit=INCREASING_DEPOSITS_COUNT
        )

        if len(recent_deposits) == INCREASING_DEPOSITS_COUNT:
            # Check if amounts are strictly increasing (newest to oldest)
            if recent_deposits[0].amount > recent_deposits[1].amount > recent_deposits[2].amount:
                return [AlertCode.ALERT_300]
        return []


class Rule123_WindowedDepositRule(Rule):
    """Rule 123: Alert on high deposit volume in time window.

    This rule checks if the total amount of deposits within a 30-second
    window exceeds the threshold (currently £200).
    """

    def evaluate(self, context: RuleContext) -> List[AlertCode]:
        """Evaluate if windowed deposit total exceeds threshold.

        Args:
            context: RuleContext containing the event to evaluate

        Returns:
            List containing ALERT_123 if threshold exceeded, empty list otherwise
        """
        window_start = max(0, context.event.t - WINDOWED_DEPOSITS_WINDOW)
        window_deposits = context.state_manager.get_user_events_by_type_time_range(
            user_id=context.event.user_id,
            event_type=EventType.DEPOSIT,
            start_time=window_start,
            end_time=context.event.t,
        )

        total_deposits = sum(event.amount for event in window_deposits)
        if total_deposits > WINDOWED_DEPOSITS_THRESHOLD:
            return [AlertCode.ALERT_123]
        return []
