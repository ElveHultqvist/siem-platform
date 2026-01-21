from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Header
import structlog

from case_service.models import Case, CaseCreate, CaseUpdate, LinkAlertRequest, CreateCommentRequest, CaseAlert, CaseComment
from case_service.database import Database
from main import db

router = APIRouter()
logger = structlog.get_logger()


def get_tenant_id(x_tenant_id: str = Header(...)) -> str:
    """Extract and validate tenant ID from header"""
    if not x_tenant_id or len(x_tenant_id) < 3:
        raise HTTPException(status_code=400, detail="Invalid X-Tenant-ID header")
    return x_tenant_id


def get_user_id(x_user_id: str = Header(default="system")) -> str:
    """Extract user ID from header (from JWT in production)"""
    return x_user_id


@router.post("/cases", response_model=Case, status_code=201)
async def create_case(
    case_data: CaseCreate,
    tenant_id: str = Depends(get_tenant_id),
    user_id: str = Depends(get_user_id)
):
    """Create a new case"""
    query = """
        INSERT INTO cases (tenant_id, title, description, severity, assigned_to, created_by)
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING id, tenant_id, title, description, severity, status, assigned_to,
                  created_at, updated_at, created_by, modified_by, metadata
    """
    
    try:
        row = await db.fetchrow(
            query,
            tenant_id,
            case_data.title,
            case_data.description,
            case_data.severity,
            case_data.assigned_to,
            user_id
        )
        
        logger.info(
            "Case created",
            tenant_id=tenant_id,
            case_id=str(row["id"]),
            created_by=user_id
        )
        
        return Case(**dict(row))
    
    except Exception as e:
        logger.error("Failed to create case", error=str(e), tenant_id=tenant_id)
        raise HTTPException(status_code=500, detail="Failed to create case")


@router.get("/cases", response_model=List[Case])
async def list_cases(
    tenant_id: str = Depends(get_tenant_id),
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """List cases for tenant with optional filtering"""
    if status:
        query = """
            SELECT id, tenant_id, title, description, severity, status, assigned_to,
                   created_at, updated_at, created_by, modified_by, metadata
            FROM cases
            WHERE tenant_id = $1 AND status = $2
            ORDER BY created_at DESC
            LIMIT $3 OFFSET $4
        """
        rows = await db.fetch(query, tenant_id, status, limit, offset)
    else:
        query = """
            SELECT id, tenant_id, title, description, severity, status, assigned_to,
                   created_at, updated_at, created_by, modified_by, metadata
            FROM cases
            WHERE tenant_id = $1
            ORDER BY created_at DESC
            LIMIT $2 OFFSET $3
        """
        rows = await db.fetch(query, tenant_id, limit, offset)
    
    return [Case(**dict(row)) for row in rows]


@router.get("/cases/{case_id}", response_model=Case)
async def get_case(
    case_id: UUID,
    tenant_id: str = Depends(get_tenant_id)
):
    """Get a specific case"""
    query = """
        SELECT id, tenant_id, title, description, severity, status, assigned_to,
               created_at, updated_at, created_by, modified_by, metadata
        FROM cases
        WHERE id = $1 AND tenant_id = $2
    """
    
    row = await db.fetchrow(query, case_id, tenant_id)
    
    if not row:
        raise HTTPException(status_code=404, detail="Case not found")
    
    return Case(**dict(row))


@router.patch("/cases/{case_id}", response_model=Case)
async def update_case(
    case_id: UUID,
    case_update: CaseUpdate,
    tenant_id: str = Depends(get_tenant_id),
    user_id: str = Depends(get_user_id)
):
    """Update a case"""
    # Build dynamic UPDATE query based on provided fields
    updates = []
    values = [case_id, tenant_id]
    param_idx = 3
    
    if case_update.title is not None:
        updates.append(f"title = ${param_idx}")
        values.append(case_update.title)
        param_idx += 1
    
    if case_update.description is not None:
        updates.append(f"description = ${param_idx}")
        values.append(case_update.description)
        param_idx += 1
    
    if case_update.severity is not None:
        updates.append(f"severity = ${param_idx}")
        values.append(case_update.severity)
        param_idx += 1
    
    if case_update.status is not None:
        updates.append(f"status = ${param_idx}")
        values.append(case_update.status)
        param_idx += 1
    
    if case_update.assigned_to is not None:
        updates.append(f"assigned_to = ${param_idx}")
        values.append(case_update.assigned_to)
        param_idx += 1
    
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    updates.append(f"modified_by = ${param_idx}")
    values.append(user_id)
    
    query = f"""
        UPDATE cases
        SET {', '.join(updates)}
        WHERE id = $1 AND tenant_id = $2
        RETURNING id, tenant_id, title, description, severity, status, assigned_to,
                  created_at, updated_at, created_by, modified_by, metadata
    """
    
    try:
        row = await db.fetchrow(query, *values)
        
        if not row:
            raise HTTPException(status_code=404, detail="Case not found")
        
        logger.info(
            "Case updated",
            tenant_id=tenant_id,
            case_id=str(case_id),
            modified_by=user_id
        )
        
        return Case(**dict(row))
    
    except Exception as e:
        logger.error("Failed to update case", error=str(e), case_id=str(case_id))
        raise HTTPException(status_code=500, detail="Failed to update case")


@router.post("/cases/{case_id}/alerts", response_model=CaseAlert, status_code=201)
async def link_alert_to_case(
    case_id: UUID,
    link_request: LinkAlertRequest,
    tenant_id: str = Depends(get_tenant_id),
    user_id: str = Depends(get_user_id)
):
    """Link an alert to a case"""
    # First verify case exists and belongs to tenant
    case_check = await db.fetchval(
        "SELECT id FROM cases WHERE id = $1 AND tenant_id = $2",
        case_id,
        tenant_id
    )
    
    if not case_check:
        raise HTTPException(status_code=404, detail="Case not found")
    
    # Link alert to case
    query = """
        INSERT INTO case_alerts (tenant_id, case_id, alert_id, linked_by)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (tenant_id, case_id, alert_id) DO NOTHING
        RETURNING id, tenant_id, case_id, alert_id, linked_at, linked_by
    """
    
    try:
        row = await db.fetchrow(
            query,
            tenant_id,
            case_id,
            link_request.alert_id,
            user_id
        )
        
        if not row:
            # Already linked
            existing = await db.fetchrow(
                "SELECT * FROM case_alerts WHERE tenant_id = $1 AND case_id = $2 AND alert_id = $3",
                tenant_id,
                case_id,
                link_request.alert_id
            )
            return CaseAlert(**dict(existing))
        
        logger.info(
            "Alert linked to case",
            tenant_id=tenant_id,
            case_id=str(case_id),
            alert_id=link_request.alert_id
        )
        
        return CaseAlert(**dict(row))
    
    except Exception as e:
        logger.error("Failed to link alert", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to link alert")


@router.get("/cases/{case_id}/alerts", response_model=List[CaseAlert])
async def get_case_alerts(
    case_id: UUID,
    tenant_id: str = Depends(get_tenant_id)
):
    """Get all alerts linked to a case"""
    query = """
        SELECT id, tenant_id, case_id, alert_id, linked_at, linked_by
        FROM case_alerts
        WHERE case_id = $1 AND tenant_id = $2
        ORDER BY linked_at DESC
    """
    
    rows = await db.fetch(query, case_id, tenant_id)
    return [CaseAlert(**dict(row)) for row in rows]


@router.post("/cases/{case_id}/comments", response_model=CaseComment, status_code=201)
async def add_comment(
    case_id: UUID,
    comment_request: CreateCommentRequest,
    tenant_id: str = Depends(get_tenant_id),
    user_id: str = Depends(get_user_id)
):
    """Add a comment to a case"""
    # Verify case exists
    case_check = await db.fetchval(
        "SELECT id FROM cases WHERE id = $1 AND tenant_id = $2",
        case_id,
        tenant_id
    )
    
    if not case_check:
        raise HTTPException(status_code=404, detail="Case not found")
    
    query = """
        INSERT INTO case_comments (tenant_id, case_id, comment, created_by)
        VALUES ($1, $2, $3, $4)
        RETURNING id, tenant_id, case_id, comment, created_at, created_by
    """
    
    try:
        row = await db.fetchrow(
            query,
            tenant_id,
            case_id,
            comment_request.comment,
            user_id
        )
        
        return CaseComment(**dict(row))
    
    except Exception as e:
        logger.error("Failed to add comment", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to add comment")


@router.get("/cases/{case_id}/comments", response_model=List[CaseComment])
async def get_case_comments(
    case_id: UUID,
    tenant_id: str = Depends(get_tenant_id)
):
    """Get all comments for a case"""
    query = """
        SELECT id, tenant_id, case_id, comment, created_at, created_by
        FROM case_comments
        WHERE case_id = $1 AND tenant_id = $2
        ORDER BY created_at ASC
    """
    
    rows = await db.fetch(query, case_id, tenant_id)
    return [CaseComment(**dict(row)) for row in rows]
