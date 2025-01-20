"""Clear router for resetting application state."""

from fastapi import APIRouter, Depends

from app.services.state_manager import StateManager

router = APIRouter(tags=["utils"])


@router.post("/clear")
async def clear(state_manager: StateManager = Depends()) -> dict[str, str]:
    """Clear all application state.

    This endpoint is primarily for testing purposes, allowing the state
    to be reset between test runs.

    Returns:
        Dict confirming the clear operation was successful
    """
    state_manager.clear()
    return {"status": "cleared"}
