from typing import Dict, Optional
from datetime import datetime
import uuid
import structlog

from detect.rules.base import BaseRule
from detect.state import StateStore

logger = structlog.get_logger()


class FailedLoginRule(BaseRule):
    """
    Detects multiple failed login attempts within a time window
    
    Rule: If category == "auth" AND failed_login_count >= 10 within 5 minutes per actor,
    emit alert
    """
    
    RULE_NAME = "failed_login_threshold"
    THRESHOLD = 10
    WINDOW_SECONDS = 300  # 5 minutes
    
    def __init__(self, state: StateStore):
        super().__init__(state, self.RULE_NAME)
        self._triggered_actors = set()  # Track actors we've already alerted for
    
    async def evaluate(self, event: Dict) -> bool:
        """
        Evaluate if this event triggers the failed login rule
        
        Returns:
            True if 10+ failed logins in 5 minutes, False otherwise
        """
        # Check if event is auth category
        if event.get("category") != "auth":
            return False
        
        # Check if it's a failed login
        attributes = event.get("attributes", {})
        if attributes.get("failed_login_count", 0) == 0:
            # Not a failed login
            return False
        
        # Check if event indicates failure
        outcome = event.get("outcome")
        if outcome and outcome != "failure":
            return False
        
        # Get actor information
        actor = event.get("actor")
        if not actor or not actor.get("id"):
            logger.debug("Event missing actor information", event_id=event.get("event_id"))
            return False
        
        tenant_id = event.get("tenant_id")
        actor_id = actor.get("id")
        
        # Create state key
        state_key = f"{tenant_id}:failed_login:{actor_id}"
        
        # Add event to state and get all events in window
        events_in_window = await self.state.add_event(
            key=state_key,
            event_data={
                "event_id": event.get("event_id"),
                "timestamp": event.get("timestamp"),
                "source_ip": attributes.get("source_ip"),
            },
            window_seconds=self.WINDOW_SECONDS
        )
        
        # Count failed logins
        failed_count = len(events_in_window)
        
        logger.debug(
            "Failed login count",
            tenant_id=tenant_id,
            actor_id=actor_id,
            count=failed_count,
            threshold=self.THRESHOLD
        )
        
        # Check if threshold exceeded
        if failed_count >= self.THRESHOLD:
            # Check if we've already alerted for this actor recently
            alert_key = f"{tenant_id}:{actor_id}"
            if alert_key in self._triggered_actors:
                logger.debug("Already alerted for actor", actor_id=actor_id)
                return False
            
            self._triggered_actors.add(alert_key)
            return True
        
        return False
    
    async def generate_alert(self, event: Dict) -> Optional[Dict]:
        """Generate alert for failed login threshold"""
        tenant_id = event.get("tenant_id")
        actor = event.get("actor", {})
        actor_id = actor.get("id")
        actor_name = actor.get("name", actor_id)
        attributes = event.get("attributes", {})
        
        # Get recent events for context
        state_key = f"{tenant_id}:failed_login:{actor_id}"
        recent_events = await self.state.add_event(
            key=state_key,
            event_data={},  # Don't add again, just get recent
            window_seconds=self.WINDOW_SECONDS
        )
        
        # Extract related event IDs
        related_event_ids = [e.get("event_id") for e in recent_events if e.get("event_id")]
        
        # Extract source IPs
        source_ips = list(set([e.get("source_ip") for e in recent_events if e.get("source_ip")]))
        
        alert = {
            "tenant_id": tenant_id,
            "alert_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "severity": 8,  # High severity
            "rule_name": self.RULE_NAME,
            "rule_description": f"Detected {len(recent_events)} failed login attempts in {self.WINDOW_SECONDS // 60} minutes",
            "actor": {
                "type": actor.get("type", "user"),
                "id": actor_id,
                "name": actor_name
            },
            "target": event.get("target"),
            "details": {
                "failed_login_count": len(recent_events),
                "threshold": self.THRESHOLD,
                "window_minutes": self.WINDOW_SECONDS // 60,
                "source_ips": source_ips,
                "first_attempt": recent_events[0].get("timestamp") if recent_events else None,
                "last_attempt": event.get("timestamp")
            },
            "related_events": related_event_ids[:10],  # Limit to 10
            "tags": ["brute-force", "authentication", "failed-login"]
        }
        
        return alert
