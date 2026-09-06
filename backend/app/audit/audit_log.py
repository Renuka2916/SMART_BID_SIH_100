import hashlib
import json
from typing import Dict, Any, Optional
from app.models.audit_log import AuditLog, AuditAction

def calculate_log_hash(log_entry: AuditLog) -> str:
    """
    Computes a deterministic SHA-256 cryptographic hash of an audit log entry.
    Used for tamper-evidence and chain-of-custody verification.
    """
    data = {
        "id": log_entry.id,
        "user_email": log_entry.user_email,
        "user_role": log_entry.user_role,
        "action": log_entry.action,
        "entity_type": log_entry.entity_type,
        "entity_id": str(log_entry.entity_id),
        "summary": log_entry.summary,
        "old_values": log_entry.old_values,
        "new_values": log_entry.new_values,
        "created_at": log_entry.created_at.isoformat() if log_entry.created_at else ""
    }
    canonical_bytes = json.dumps(data, sort_keys=True).encode("utf-8")
    return hashlib.sha256(canonical_bytes).hexdigest()
