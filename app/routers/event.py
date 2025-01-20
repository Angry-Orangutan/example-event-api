from fastapi import APIRouter, Depends

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


@router.post("", response_model=EventResponse)
async def event(
    request: EventRequest,
    state_manager: StateManager = Depends(),
) -> EventResponse:
    # Save event to state manager
    state_manager.save_event(request)

    # Register all rules
    rule_manager = RuleManager()
    rule_manager.register_rule(Rule1100_LargeWithdrawalRule())
    rule_manager.register_rule(Rule30_ConsecutiveWithdrawalsRule())
    rule_manager.register_rule(Rule300_IncreasingDepositsRule())
    rule_manager.register_rule(Rule123_WindowedDepositRule())

    # Evaluate rules
    alert_codes = rule_manager.evaluate_rules(request, state_manager)

    return EventResponse(alert_codes=alert_codes, user_id=request.user_id)
