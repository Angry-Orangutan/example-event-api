from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

from app.models.alert import AlertCode
from app.models.event import EventRequest
from app.services.state_manager import StateManager


@dataclass
class RuleContext:
    """Context object containing all necessary data for rule evaluation"""

    event: EventRequest
    state_manager: StateManager


class Rule(ABC):
    """Abstract base class for all rules"""

    @abstractmethod
    def evaluate(self, context: RuleContext) -> List[AlertCode]:
        """Evaluate the rule and return any triggered alert codes"""
        pass
