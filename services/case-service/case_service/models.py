from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field


class CaseBase(BaseModel):
    """Base case model"""
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    severity: int = Field(..., ge=0, le=10)
    assigned_to: Optional[str] = None


class CaseCreate(CaseBase):
    """Model for creating a new case"""
    pass


class CaseUpdate(BaseModel):
    """Model for updating an existing case"""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    severity: Optional[int] = Field(None, ge=0, le=10)
    status: Optional[str] = Field(None, pattern="^(open|investigating|contained|resolved|closed|false_positive)$")
    assigned_to: Optional[str] = None


class Case(CaseBase):
    """Full case model"""
    id: UUID
    tenant_id: str
    status: str
    created_at: datetime
    updated_at: datetime
    created_by: str
    modified_by: Optional[str] = None
    metadata: dict = {}
    
    class Config:
        from_attributes = True


class CaseAlert(BaseModel):
    """Model for linking alert to case"""
    id: UUID
    tenant_id: str
    case_id: UUID
    alert_id: str
    linked_at: datetime
    linked_by: str
    
    class Config:
        from_attributes = True


class LinkAlertRequest(BaseModel):
    """Request to link an alert to a case"""
    alert_id: str = Field(..., min_length=1)


class CaseComment(BaseModel):
    """Model for case comment"""
    id: UUID
    tenant_id: str
    case_id: UUID
    comment: str
    created_at: datetime
    created_by: str
    
    class Config:
        from_attributes = True


class CreateCommentRequest(BaseModel):
    """Request to create a comment"""
    comment: str = Field(..., min_length=1)
