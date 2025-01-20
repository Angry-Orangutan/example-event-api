from typing import Generator

import pytest

from app.services.state_manager import StateManager


@pytest.fixture
def state_manager() -> Generator[StateManager, None, None]:
    """Fixture to provide a clean StateManager instance.

    Yields:
        StateManager: A clean instance of the state manager
    """
    manager = StateManager()
    manager.clear()
    yield manager
    manager.clear()


@pytest.fixture(autouse=True)
def clear_state() -> Generator[None, None, None]:
    """Clear state manager before and after each test.

    This fixture ensures each test starts with a clean state and
    cleans up after itself.

    Yields:
        None: This fixture doesn't yield any value
    """
    StateManager().clear()
    yield
    StateManager().clear()
