from fastapi import FastAPI

from app.routers import event
from app.services.state_manager import StateManager
from app.utils import health_check

app = FastAPI(
    title="Midnite API",
    description="Midnite API",
    version="1.0.0",
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)


def get_state_manager() -> StateManager:
    return StateManager()


# Register dependencies
app.dependency_overrides[StateManager] = get_state_manager

app.include_router(health_check.router)
app.include_router(event.router)
