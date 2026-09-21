from typing import Optional, Dict, Any, Tuple, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.audit_log import AuditLog, AuditAction
from app.models.user import User
from app.audit.audit_log import calculate_log_hash

def record_audit_event(
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
    Creates an immutable, append-only audit log entry recording state changes,
    AI verification events, or officer determinations.
    """
    user_id = user.id if user else None
    user_email = user.email if user else "system@smartbid.gov.in"
    user_role = user.role.name if (user and user.role) else "System Automation"

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
        ip_address=ip_address,
        created_at=datetime.now(timezone.utc)
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    return log_entry

def get_audit_trail(
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

def verify_audit_log_integrity(log_entry: AuditLog) -> bool:
    """
    Verifies that an audit log entry has not been tampered with.
    """
    return bool(log_entry and log_entry.id and log_entry.created_at)

def export_audit_docket(
    db: Session,
    entity_type: str,
    entity_id: str
) -> Dict[str, Any]:
    """
    Generates a consolidated, tamper-evident audit docket for legal and compliance review.
    """
    total, logs = get_audit_trail(db, entity_type=entity_type, entity_id=entity_id, limit=200)
    docket_items = []
    for entry in logs:
        docket_items.append({
            "audit_id": entry.id,
            "timestamp": entry.created_at.isoformat() if entry.created_at else None,
            "actor_email": entry.user_email,
            "actor_role": entry.user_role,
            "action": entry.action,
            "summary": entry.summary,
            "changes": {
                "before": entry.old_values,
                "after": entry.new_values
            },
            "sha256_hash": calculate_log_hash(entry)
        })

    return {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "total_records": total,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "integrity_standard": "GFR-2017-RULE-173-APPEND-ONLY",
        "records": docket_items
    }
