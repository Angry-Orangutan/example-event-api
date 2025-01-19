from fastapi import APIRouter

from app.models.event import EventRequest

router = APIRouter(prefix="/event", tags=["event"])


@router.post("")
async def event(request: EventRequest):
    return {"hello": request.name}
