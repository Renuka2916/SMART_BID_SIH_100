from typing import Optional, Dict, Any, Tuple, List
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.audit_log import AuditLog
from app.models.user import User

def record_audit_log(
    db: Session,
    user: Optional[User],
    action: str,
    entity_type: str,
    entity_id: str,
    summary: str,
    old_values: Optional[Dict[str, Any]] = None,
    new_values: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None
) -> AuditLog:
    """
    Creates an immutable, append-only audit log entry recording state changes or operational events.
    """
    user_id = user.id if user else None
    user_email = user.email if user else "system@gem.gov.in"
    user_role = user.role.name if (user and user.role) else "System"

    log_entry = AuditLog(
        user_id=user_id,
        user_email=user_email,
        user_role=user_role,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id),
        summary=summary,
        old_values=old_values,
        new_values=new_values,
        ip_address=ip_address
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    return log_entry

def get_audit_logs(
    db: Session,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    action: Optional[str] = None,
    skip: int = 0,
    limit: int = 50
) -> Tuple[int, List[AuditLog]]:
    """
    Queries paginated audit logs with optional filtering.
    """
    query = db.query(AuditLog)
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    if entity_id:
        query = query.filter(AuditLog.entity_id == str(entity_id))
    if action:
        query = query.filter(AuditLog.action == action)

    total = query.count()
    items = query.order_by(desc(AuditLog.created_at)).offset(skip).limit(limit).all()
    return total, items
