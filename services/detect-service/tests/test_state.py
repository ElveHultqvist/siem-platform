import pytest
import asyncio
from datetime import datetime, timedelta

from detect.state import StateStore


@pytest.mark.asyncio
async def test_state_store_add_event():
    """Test adding events to state store"""
    store = StateStore()
    
    # Add event
    events = await store.add_event(
        key="tenant1:user123",
        event_data={"event_id": "evt1"},
        window_seconds=300
    )
    
    assert len(events) == 1
    assert events[0]["event_id"] == "evt1"


@pytest.mark.asyncio
async def test_state_store_time_window():
    """Test time window filtering"""
    store = StateStore()
    
    # Add multiple events
    for i in range(5):
        await store.add_event(
            key="tenant1:user123",
            event_data={"event_id": f"evt{i}"},
            window_seconds=300
        )
    
    # All events should be in window
    count = await store.get_count("tenant1:user123", window_seconds=300)
    assert count == 5


@pytest.mark.asyncio
async def test_state_store_expiration():
    """Test that old events are expired"""
    store = StateStore()
    
    # Manually add old event
    old_time = (datetime.utcnow() - timedelta(minutes=10)).isoformat()
    store._store["tenant1:user123"] = [
        {"event_id": "old", "_stored_at": old_time}
    ]
    
    # Add new event
    events = await store.add_event(
        key="tenant1:user123",
        event_data={"event_id": "new"},
        window_seconds=300
    )
    
    # Old event should be filtered out
    assert len(events) == 1
    assert events[0]["event_id"] == "new"


@pytest.mark.asyncio
async def test_state_store_clear():
    """Test clearing state"""
    store = StateStore()
    
    await store.add_event(
        key="tenant1:user123",
        event_data={"event_id": "evt1"},
        window_seconds=300
    )
    
    await store.clear_key("tenant1:user123")
    
    count = await store.get_count("tenant1:user123", window_seconds=300)
    assert count == 0
