from typing import Dict, List, Optional
from datetime import datetime
import structlog

from detect.state import StateStore
from detect.rules.failed_login import FailedLoginRule

logger = structlog.get_logger()


class DetectionEngine:
    """Main detection engine that runs rules against events"""
    
    def __init__(self):
        self.state = StateStore()
        self.rules = [
            FailedLoginRule(self.state)
        ]
        logger.info("Detection engine initialized", rules_count=len(self.rules))
    
    async def process_event(self, event: Dict) -> List[Dict]:
        """
        Process an event through all detection rules
        
        Args:
            event: Normalized event dict
        
        Returns:
            List of alerts generated
        """
        alerts = []
        
        tenant_id = event.get("tenant_id")
        event_id = event.get("event_id")
        
        if not tenant_id:
            logger.warning("Event missing tenant_id", event_id=event_id)
            return alerts
        
        logger.debug(
            "Processing event",
            tenant_id=tenant_id,
            event_id=event_id,
            category=event.get("category")
        )
        
        # Run all rules
        for rule in self.rules:
            try:
                if await rule.evaluate(event):
                    alert = await rule.generate_alert(event)
                    if alert:
                        alerts.append(alert)
                        logger.info(
                            "Alert generated",
                            tenant_id=tenant_id,
                            rule_name=rule.name,
                            alert_id=alert.get("alert_id"),
                            severity=alert.get("severity")
                        )
            except Exception as e:
                logger.error(
                    "Rule evaluation failed",
                    rule_name=rule.name,
                    error=str(e),
                    tenant_id=tenant_id,
                    event_id=event_id
                )
        
        return alerts
    
    async def get_stats(self) -> Dict:
        """Get detection engine statistics"""
        state_stats = await self.state.get_stats()
        return {
            "rules_loaded": len(self.rules),
            "state_store": state_stats
        }
