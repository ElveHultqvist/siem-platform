import pytest
from detect.rules.failed_login import FailedLoginRule
from detect.state import StateStore


@pytest.mark.asyncio
async def test_failed_login_rule_triggers():
    """Test that failed login rule triggers after threshold"""
    store = StateStore()
    rule = FailedLoginRule(store)
    
    # Create base event
    base_event = {
        "tenant_id": "test-tenant",
        "event_id": "evt1",
        "timestamp": "2024-01-01T00:00:00Z",
        "category": "auth",
        "outcome": "failure",
        "actor": {"id": "user123", "name": "John Doe"},
        "attributes": {"failed_login_count": 1, "source_ip": "1.2.3.4"}
    }
    
    # First 9 attempts should not trigger
    for i in range(9):
        event = {**base_event, "event_id": f"evt{i}"}
        result = await rule.evaluate(event)
        assert result is False
    
    # 10th attempt should trigger
    event = {**base_event, "event_id": "evt10"}
    result = await rule.evaluate(event)
    assert result is True
    
    # Should generate alert
    alert = await rule.generate_alert(event)
    assert alert is not None
    assert alert["tenant_id"] == "test-tenant"
    assert alert["severity"] == 8
    assert alert["rule_name"] == "failed_login_threshold"


@pytest.mark.asyncio
async def test_failed_login_rule_wrong_category():
    """Test that rule ignores non-auth events"""
    store = StateStore()
    rule = FailedLoginRule(store)
    
    event = {
        "tenant_id": "test-tenant",
        "event_id": "evt1",
        "category": "network",  # Not auth
        "outcome": "failure",
        "actor": {"id": "user123"},
        "attributes": {"failed_login_count": 1}
    }
    
    result = await rule.evaluate(event)
    assert result is False


@pytest.mark.asyncio
async def test_failed_login_rule_success_outcome():
    """Test that rule ignores successful logins"""
    store = StateStore()
    rule = FailedLoginRule(store)
    
    event = {
        "tenant_id": "test-tenant",
        "event_id": "evt1",
        "category": "auth",
        "outcome": "success",  # Success, not failure
        "actor": {"id": "user123"},
        "attributes": {"failed_login_count": 1}
    }
    
    result = await rule.evaluate(event)
    assert result is False
