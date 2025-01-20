import pytest
from pydantic import ValidationError

from app.models.alert import AlertCode
from app.models.event import EventResponse


def test_alert_computed_property():
    # Test when alert_codes is empty
    response = EventResponse(user_id=1)
    assert response.alert is False
    assert response.alert_codes == []

    # Test when alert_codes has one code
    response = EventResponse(alert_codes=[AlertCode.ALERT_1100], user_id=1)
    assert response.alert is True

    # Test when alert_codes has multiple codes
    response = EventResponse(alert_codes=[AlertCode.ALERT_1100, AlertCode.ALERT_300], user_id=1)
    assert response.alert is True


def test_user_id_required():
    # Test that user_id is required
    with pytest.raises(ValidationError):
        EventResponse()  # type: ignore

    # Test that user_id cannot be None
    with pytest.raises(ValidationError):
        EventResponse(user_id=None)  # type: ignore


def test_alert_codes_validation():
    # Test that alert_codes accepts valid AlertCode values
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

    # Test that invalid alert codes are rejected
    with pytest.raises(ValidationError):
        EventResponse(alert_codes=["invalid_code"], user_id=1)  # type: ignore

    # Test that non-list values are rejected
    with pytest.raises(ValidationError):
        EventResponse(alert_codes="not_a_list", user_id=1)  # type: ignore
