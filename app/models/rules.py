from decimal import Decimal
from typing import List

from app.models.alert import AlertCode
from app.models.event import EventType
from app.models.rule import Rule, RuleContext


class Rule1100_LargeWithdrawalRule(Rule):
    """Rule 1100: Alert when withdrawal amount is over 100"""

    def evaluate(self, context: RuleContext) -> List[AlertCode]:
        if context.event.type == EventType.WITHDRAW and context.event.amount > Decimal("100"):
            return [AlertCode.ALERT_1100]
        return []


class Rule30_ConsecutiveWithdrawalsRule(Rule):
    """Rule 30: Alert on 3 consecutive withdrawals"""

    def evaluate(self, context: RuleContext) -> List[AlertCode]:
        recent_events = context.state_manager.get_user_events(context.event.user_id, limit=3)
        if len(recent_events) == 3 and all(event.type == EventType.WITHDRAW for event in recent_events):
            return [AlertCode.ALERT_30]
        return []


class Rule300_IncreasingDepositsRule(Rule):
    """Rule 300: Alert on 3 consecutive increasing deposits"""

    def evaluate(self, context: RuleContext) -> List[AlertCode]:
        recent_deposits = context.state_manager.get_user_events_by_type(
            user_id=context.event.user_id, event_type=EventType.DEPOSIT, limit=3
        )
        if len(recent_deposits) == 3:
            if recent_deposits[0].amount > recent_deposits[1].amount > recent_deposits[2].amount:
                return [AlertCode.ALERT_300]
        return []


class Rule123_WindowedDepositRule(Rule):
    """Rule 123: Alert when accumulative deposit amount over 30 seconds is over 200"""

    def evaluate(self, context: RuleContext) -> List[AlertCode]:
        window_start = context.event.t - 30
        window_deposits = context.state_manager.get_user_events_by_type_time_range(
            user_id=context.event.user_id,
            event_type=EventType.DEPOSIT,
            start_time=window_start,
            end_time=context.event.t,
        )

        total_deposits = sum(event.amount for event in window_deposits)
        if total_deposits > Decimal("200"):
            return [AlertCode.ALERT_123]
        return []
