from decimal import Decimal

from fastapi import APIRouter, Depends

from app.models.alert import AlertCode
from app.models.event import EventRequest, EventResponse, EventType
from app.services.state_manager import StateManager

router = APIRouter(prefix="/event", tags=["event"])


@router.post("", response_model=EventResponse)
async def event(request: EventRequest, state_manager: StateManager = Depends()) -> EventResponse:
    alert_codes: list[AlertCode] = []

    # Save event to state manager
    state_manager.save_event(request)

    # Rule 1: Alert 1100 - Withdrawal amount over 100
    if request.type == EventType.WITHDRAW and request.amount > Decimal("100"):
        alert_codes.append(AlertCode.ALERT_1100)

    # Rule 2: Alert 30 - 3 consecutive withdrawals
    recent_events = state_manager.get_user_events(request.user_id, limit=3)
    if len(recent_events) == 3 and all(event.type == EventType.WITHDRAW for event in recent_events):
        alert_codes.append(AlertCode.ALERT_30)

    # Rule 3: Alert 300 - 3 consecutive increasing deposits
    recent_deposits = state_manager.get_user_events_by_type(
        user_id=request.user_id, event_type=EventType.DEPOSIT, limit=3
    )
    if len(recent_deposits) == 3:
        # Check if deposits are strictly increasing (most recent first)
        if recent_deposits[0].amount > recent_deposits[1].amount > recent_deposits[2].amount:
            alert_codes.append(AlertCode.ALERT_300)

    # Rule 4: Alert 123 - Accumulative deposit amount over a window of 30 seconds is over 200
    window_start = request.t - 30  # 30 seconds ago
    window_deposits = state_manager.get_user_events_by_type_time_range(
        user_id=request.user_id, event_type=EventType.DEPOSIT, start_time=window_start, end_time=request.t
    )

    total_deposits = sum(event.amount for event in window_deposits)
    if total_deposits > Decimal("200"):
        alert_codes.append(AlertCode.ALERT_123)

    return EventResponse(alert_codes=alert_codes, user_id=request.user_id)
