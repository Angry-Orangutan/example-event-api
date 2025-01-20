"""Alert codes for rules."""

from enum import Enum, unique


@unique
class AlertCode(Enum):
    """Enum of valid alert codes."""

    ALERT_30 = 30  # Three consecutive withdrawals
    ALERT_123 = 123  # More than 3 deposits in a 1-minute window
    ALERT_300 = 300  # Increasing deposits pattern detected
    ALERT_1100 = 1100  # Large withdrawal after deposit pattern
