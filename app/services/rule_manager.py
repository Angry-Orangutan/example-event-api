"""Rule manager for handling rule registration and evaluation.

This module provides the RuleManager class that handles registration and evaluation
of rules. It maintains a list of rules and evaluates them in sequence
for each event.
"""

from typing import List, Sequence

from app.models.alert import AlertCode
from app.models.event import EventRequest
from app.models.rule import Rule, RuleContext
from app.services.state_manager import StateManager


class RuleManager:
    """Manages the registration and evaluation of rules.

    This class maintains a list of rules and provides methods to register new rules
    and evaluate all registered rules against events.

    Attributes:
        _rules: List of registered Rule instances
    """

    def __init__(self) -> None:
        """Initialize an empty rule manager."""
        self._rules: List[Rule] = []

    def register_rule(self, rule: Rule) -> None:
        """Register a new rule for evaluation.

        Args:
            rule: The Rule instance to register

        Raises:
            ValueError: If rule is None or already registered
        """
        if rule is None:
            raise ValueError("Cannot register None as a rule")
        if rule in self._rules:
            raise ValueError(f"Rule {rule.__class__.__name__} is already registered")
        self._rules.append(rule)

    def register_rules(self, rules: Sequence[Rule]) -> None:
        """Register multiple rules at once.

        Args:
            rules: Sequence of Rule instances to register

        Raises:
            ValueError: If any rule is None or already registered
        """
        for rule in rules:
            self.register_rule(rule)

    def evaluate_rules(self, event: EventRequest, state_manager: StateManager) -> List[AlertCode]:
        """Evaluate all registered rules for the given event.

        Args:
            event: The event to evaluate rules against
            state_manager: StateManager instance for accessing event history

        Returns:
            List of AlertCodes from triggered rules

        Raises:
            ValueError: If event or state_manager is None
        """
        if event is None:
            raise ValueError("Cannot evaluate rules with None event")
        if state_manager is None:
            raise ValueError("Cannot evaluate rules with None state manager")

        context = RuleContext(event=event, state_manager=state_manager)
        alert_codes: List[AlertCode] = []

        for rule in self._rules:
            try:
                alert_codes.extend(rule.evaluate(context))
            except Exception as e:
                # Log the error but continue evaluating other rules
                # TODO: Add proper logging
                print(f"Error evaluating rule {rule.__class__.__name__}: {str(e)}")
                continue

        return alert_codes

    def clear_rules(self) -> None:
        """Remove all registered rules."""
        self._rules.clear()
