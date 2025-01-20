"""Unit tests for the EventResponse model.

This module contains tests for validating the EventResponse model's
behavior, including alert code handling, user ID validation, and
computed properties.
"""

import pytest
from pydantic import ValidationError

from app.models.alert import AlertCode
from app.models.event import EventResponse


@pytest.mark.parametrize(
    "alert_codes,expected_alert",
    [
        ([], False),  # Empty alert codes
        ([AlertCode.ALERT_1100], True),  # Single alert code
        ([AlertCode.ALERT_1100, AlertCode.ALERT_300], True),  # Multiple alert codes
    ],
)
def test_alert_computed_property(alert_codes: list[AlertCode], expected_alert: bool) -> None:
    """Test that the alert computed property works correctly.

    Args:
        alert_codes: List of alert codes to test
        expected_alert: Expected value of the alert property
    """
    response = EventResponse(alert_codes=alert_codes, user_id=1)
    assert response.alert is expected_alert
    assert response.alert_codes == alert_codes


@pytest.mark.parametrize(
    "invalid_input",
    [
        {},  # Missing user_id
        {"user_id": None},  # None user_id
        {"user_id": 0},  # Zero user_id
        {"user_id": -1},  # Negative user_id
    ],
)
def test_user_id_validation(invalid_input: dict) -> None:
    """Test that user_id validation works correctly.

    Args:
        invalid_input: Dictionary containing invalid user_id values
    """
    with pytest.raises(ValidationError):
        EventResponse(**invalid_input)  # type: ignore


def test_valid_alert_codes() -> None:
    """Test that valid alert codes are accepted."""
    response = EventResponse(
        alert_codes=[
            AlertCode.ALERT_30,
            AlertCode.ALERT_123,
            AlertCode.ALERT_300,
            AlertCode.ALERT_1100,
        ],
        user_id=1,
    )
    assert len(response.alert_codes) == 4
    assert all(isinstance(code, AlertCode) for code in response.alert_codes)


@pytest.mark.parametrize(
    "invalid_codes",
    [
        ["invalid_code"],  # Invalid alert code string
        "not_a_list",  # Not a list
        [None],  # None value
    ],
)
def test_invalid_alert_codes(invalid_codes: list) -> None:
    """Test that invalid alert codes are rejected.

    Args:
        invalid_codes: List of invalid alert code values
    """
    with pytest.raises(ValidationError):
        EventResponse(alert_codes=invalid_codes, user_id=1)  # type: ignore
