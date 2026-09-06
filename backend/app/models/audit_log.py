from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, event
from database import Base

class AuditAction(str, Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    VERIFY = "VERIFY"
    STATUS_CHANGE = "STATUS_CHANGE"
    DOCUMENT_UPLOAD = "DOCUMENT_UPLOAD"
    DECISION_OVERRIDE = "DECISION_OVERRIDE"

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    user_email = Column(String(255), nullable=False, index=True)
    user_role = Column(String(50), nullable=False)

    action = Column(String(50), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False, index=True)  # TENDER, BIDDER, DOCUMENT, COMPLIANCE_CHECK, USER
    entity_id = Column(String(100), nullable=False, index=True)
    summary = Column(String(500), nullable=False)

    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    ip_address = Column(String(50), nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

# Enforce Append-Only Immutability at SQLAlchemy ORM Level
@event.listens_for(AuditLog, "before_update")
def prevent_audit_log_update(mapper, connection, target):
    raise RuntimeError("AuditLog records are strictly immutable and cannot be updated.")

@event.listens_for(AuditLog, "before_delete")
def prevent_audit_log_delete(mapper, connection, target):
    raise RuntimeError("AuditLog records are strictly immutable and cannot be deleted.")
