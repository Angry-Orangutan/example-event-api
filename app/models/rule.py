"""Rule model for defining rules.

This module provides the base Rule class and RuleContext for implementing
rules. Each rule can evaluate an event in the context of
historical events and return alert codes if a pattern is detected.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

from app.models.alert import AlertCode
from app.models.event import EventRequest
from app.services.state_manager import StateManager


@dataclass(frozen=True)
class RuleContext:
    """Context object containing all necessary data for rule evaluation.

    This immutable dataclass holds the event being evaluated and provides
    access to historical events through the state manager.

    Attributes:
        event: The event being evaluated
        state_manager: StateManager instance for accessing event history
    """

    event: EventRequest
    state_manager: StateManager

    def __post_init__(self) -> None:
        """Validate the context attributes."""
        if self.event is None:
            raise ValueError("Event cannot be None")
        if self.state_manager is None:
            raise ValueError("StateManager cannot be None")


class Rule(ABC):
    """Abstract base class for all rules.

    This class defines the interface that all rules must implement.
    Each rule evaluates an event in the context of historical events
    and returns alert codes if patterns are detected.
    """

    @abstractmethod
    def evaluate(self, context: RuleContext) -> List[AlertCode]:
        """Evaluate the rule and return any triggered alert codes.

        Args:
            context: RuleContext containing the event and state manager

        Returns:
            List of AlertCodes if patterns are detected, empty list otherwise

        Raises:
            ValueError: If context is None or invalid
        """
        raise NotImplementedError("Rule must implement evaluate method")

    def get_description(self) -> str:
        """Get a human-readable description of what this rule checks for.

        Returns:
            String description of the rule's purpose
        """
        return self.__class__.__doc__ or "No description available"
