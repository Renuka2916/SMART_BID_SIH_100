from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from app.models.user import User
from app.schemas.audit_schema import AuditLogListResponse
from app.api.auth import get_current_user
from app.services.audit_service import get_audit_logs

router = APIRouter(prefix="/audit-logs", tags=["Audit & Traceability"])

@router.get("", response_model=AuditLogListResponse)
def query_audit_trail(
    entity_type: Optional[str] = Query(None, description="Filter by entity: TENDER, BIDDER, DOCUMENT, COMPLIANCE_CHECK"),
    entity_id: Optional[str] = Query(None, description="Filter by specific entity ID"),
    action: Optional[str] = Query(None, description="Filter by action: CREATE, UPDATE, DELETE, STATUS_CHANGE, etc."),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns paginated, immutable audit trail for legal compliance and procurement review.
    All record changes are permanently logged and tamper-proof.
    """
    total, items = get_audit_logs(
        db=db,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        skip=skip,
        limit=limit
    )
    return AuditLogListResponse(total=total, items=items)
