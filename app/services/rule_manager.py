from typing import List

from app.models.alert import AlertCode
from app.models.event import EventRequest
from app.models.rule import Rule, RuleContext
from app.services.state_manager import StateManager


class RuleManager:
    """Manages the registration and evaluation of rules"""

    def __init__(self) -> None:
        self._rules: List[Rule] = []

    def register_rule(self, rule: Rule) -> None:
        """Register a new rule"""
        self._rules.append(rule)

    def evaluate_rules(self, event: EventRequest, state_manager: StateManager) -> List[AlertCode]:
        """Evaluate all registered rules for the given event"""
        context = RuleContext(event=event, state_manager=state_manager)
        alert_codes: List[AlertCode] = []

        for rule in self._rules:
            alert_codes.extend(rule.evaluate(context))

        return alert_codes
