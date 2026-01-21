from abc import ABC, abstractmethod
from typing import Dict, Optional
from detect.state import StateStore


class BaseRule(ABC):
    """Base class for detection rules"""
    
    def __init__(self, state: StateStore, name: str):
        self.state = state
        self.name = name
    
    @abstractmethod
    async def evaluate(self, event: Dict) -> bool:
        """
        Evaluate if the rule matches the event
        
        Returns:
            True if rule triggers, False otherwise
        """
        pass
    
    @abstractmethod
    async def generate_alert(self, event: Dict) -> Optional[Dict]:
        """
        Generate an alert dict if rule triggered
        
        Returns:
            Alert dict or None
        """
        pass
