"""Unit tests for StateManager locking functionality.

This module contains tests for the distributed locking mechanism
implemented in the StateManager, including lock acquisition,
release, and timeout behavior.
"""

import time

import pytest

from app.services.state_manager import StateManager
from tests.utils.fixtures import state_manager  # noqa: F401


@pytest.mark.usefixtures("state_manager")
def test_acquire_lock_success(state_manager: StateManager) -> None:  # noqa: F811
    """Test successful lock acquisition.

    This test verifies that a lock can be acquired when no other
    process holds it.
    """
    assert state_manager.acquire_lock(1) is True


@pytest.mark.usefixtures("state_manager")
def test_acquire_lock_fails_when_already_locked(state_manager: StateManager) -> None:  # noqa: F811
    """Test lock acquisition failure when already locked.

    This test verifies that a lock cannot be acquired when another
    process already holds it.
    """

    # First acquisition should succeed
    assert state_manager.acquire_lock(1) is True

    # Second acquisition should fail
    assert state_manager.acquire_lock(1) is False


@pytest.mark.usefixtures("state_manager")
def test_release_lock_allows_reacquisition(state_manager: StateManager) -> None:  # noqa: F811
    """Test lock reacquisition after release.

    This test verifies that a lock can be reacquired after it has
    been released by the previous holder.
    """

    # Acquire initial lock
    assert state_manager.acquire_lock(1) is True

    # Release the lock
    state_manager.release_lock(1)

    # Should be able to acquire again
    assert state_manager.acquire_lock(1) is True


@pytest.mark.usefixtures("state_manager")
def test_lock_timeout(state_manager: StateManager) -> None:  # noqa: F811
    """Test lock timeout behavior.

    This test verifies that a lock automatically expires after
    its timeout period, allowing reacquisition.
    """

    # Set a very short timeout for this test
    original_timeout = state_manager.get_lock_timeout()
    state_manager.set_lock_timeout(1)

    try:
        # Acquire initial lock
        assert state_manager.acquire_lock(1) is True

        # Wait for lock to expire
        time.sleep(1.1)

        # Should be able to acquire again after timeout
        assert state_manager.acquire_lock(1) is True
    finally:
        # Restore original timeout
        state_manager.set_lock_timeout(original_timeout)


@pytest.mark.usefixtures("state_manager")
def test_different_users_can_acquire_locks_simultaneously(state_manager: StateManager) -> None:  # noqa: F811
    """Test concurrent lock acquisition by different users.

    This test verifies that different users can hold locks
    simultaneously without interference.
    """

    # First user acquires lock
    assert state_manager.acquire_lock(1) is True

    # Second user should also be able to acquire lock
    assert state_manager.acquire_lock(2) is True


@pytest.mark.usefixtures("state_manager")
def test_lock_timeout_validation(state_manager: StateManager) -> None:  # noqa: F811
    """Test lock timeout validation.

    This test verifies that invalid timeout values are rejected.
    """

    with pytest.raises(ValueError, match="Lock timeout must be at least 1 second"):
        state_manager.set_lock_timeout(0)

    with pytest.raises(ValueError, match="Lock timeout must be at least 1 second"):
        state_manager.set_lock_timeout(-1)
