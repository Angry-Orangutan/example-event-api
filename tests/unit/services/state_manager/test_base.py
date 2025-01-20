import pytest

from app.services.state_manager import StateManager


@pytest.fixture
def state_manager():
    manager = StateManager()
    manager.clear()  # Ensure clean state
    return manager


def test_singleton_pattern():
    """Test that StateManager is a singleton."""
    manager1 = StateManager()
    manager2 = StateManager()
    assert manager1 is manager2
