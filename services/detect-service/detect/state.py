import asyncio
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import structlog

logger = structlog.get_logger()


class StateStore:
    """In-memory state store for detection rules with time-window support"""
    
    def __init__(self):
        self._store: Dict[str, List[Dict]] = {}
        self._lock = asyncio.Lock()
    
    async def add_event(self, key: str, event_data: Dict, window_seconds: int) -> List[Dict]:
        """
        Add event to state and return all events within the time window
        
        Args:
            key: State key (e.g., "tenant_id:actor_id")
            event_data: Event data to store
            window_seconds: Time window in seconds
        
        Returns:
            List of events within the time window
        """
        async with self._lock:
            now = datetime.utcnow()
            cutoff = now - timedelta(seconds=window_seconds)
            
            # Initialize if key doesn't exist
            if key not in self._store:
                self._store[key] = []
            
            # Add timestamp to event
            event_data["_stored_at"] = now.isoformat()
            
            # Add new event
            self._store[key].append(event_data)
            
            # Remove expired events
            self._store[key] = [
                e for e in self._store[key]
                if datetime.fromisoformat(e["_stored_at"]) > cutoff
            ]
            
            logger.debug(
                "State updated",
                key=key,
                events_in_window=len(self._store[key]),
                window_seconds=window_seconds
            )
            
            return self._store[key]
    
    async def get_count(self, key: str, window_seconds: int) -> int:
        """Get count of events within time window"""
        async with self._lock:
            if key not in self._store:
                return 0
            
            now = datetime.utcnow()
            cutoff = now - timedelta(seconds=window_seconds)
            
            # Count events within window
            count = sum(
                1 for e in self._store[key]
                if datetime.fromisoformat(e["_stored_at"]) > cutoff
            )
            
            return count
    
    async def clear_key(self, key: str):
        """Clear state for a specific key"""
        async with self._lock:
            if key in self._store:
                del self._store[key]
    
    async def get_stats(self) -> Dict:
        """Get state store statistics"""
        async with self._lock:
            return {
                "total_keys": len(self._store),
                "total_events": sum(len(events) for events in self._store.values())
            }
