"""Main application module for the Midnite API."""

from typing import Final

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import clear, event, health
from app.services.state_manager import StateManager

# API metadata constants
API_TITLE: Final[str] = "Midnite API"
API_DESCRIPTION: Final[str] = """
Midnite API for processing financial transactions and detecting suspicious patterns.
"""
API_VERSION: Final[str] = "1.0.0"

# Create FastAPI application
app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all - incase Midnite test via browser
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create shared state manager instance
state_manager = StateManager()


def get_state_manager() -> StateManager:
    """Dependency provider for the state manager."""
    return state_manager


# Register dependencies
app.dependency_overrides[StateManager] = get_state_manager

# Register routers
app.include_router(health.router)
app.include_router(event.router)
app.include_router(clear.router)
