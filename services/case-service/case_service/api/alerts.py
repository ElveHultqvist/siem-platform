from typing import List
from fastapi import APIRouter, Depends, HTTPException, Header
import structlog

from case_service.models import CaseAlert
from main import db

router = APIRouter()
logger = structlog.get_logger()


def get_tenant_id(x_tenant_id: str = Header(...)) -> str:
    """Extract and validate tenant ID from header"""
    if not x_tenant_id or len(x_tenant_id) < 3:
        raise HTTPException(status_code=400, detail="Invalid X-Tenant-ID header")
    return x_tenant_id


@router.get("/alerts/{alert_id}/cases", response_model=List[CaseAlert])
async def get_alert_cases(
    alert_id: str,
    tenant_id: str = Depends(get_tenant_id)
):
    """Get all cases linked to an alert"""
    query = """
        SELECT id, tenant_id, case_id, alert_id, linked_at, linked_by
        FROM case_alerts
        WHERE alert_id = $1 AND tenant_id = $2
        ORDER BY linked_at DESC
    """
    
    rows = await db.fetch(query, alert_id, tenant_id)
    return [CaseAlert(**dict(row)) for row in rows]
