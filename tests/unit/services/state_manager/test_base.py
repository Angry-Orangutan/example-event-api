"""Unit tests for StateManager base functionality.

This module contains tests for the core functionality of the StateManager,
including singleton pattern and initialization.
"""

import pytest

from app.services.state_manager import StateManager
from tests.utils.fixtures import state_manager  # noqa: F401


@pytest.mark.usefixtures("state_manager")
def test_singleton_pattern(state_manager: StateManager) -> None:  # noqa: F811
    """Test that StateManager follows the singleton pattern.

    This test verifies that multiple instantiations of StateManager
    return the same instance.
    """
    manager1 = StateManager()
    manager2 = StateManager()

    assert state_manager is manager1
    assert id(state_manager) == id(manager1)

    assert manager1 is manager2
    assert id(manager1) == id(manager2)


@pytest.mark.usefixtures("state_manager")
def test_redis_initialization(state_manager: StateManager) -> None:  # noqa: F811
    """Test that Redis is properly initialized."""
    assert state_manager.redis is not None
    assert state_manager.redis.ping()  # type: ignore
