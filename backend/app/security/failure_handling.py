import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.bidder import Bidder
from app.models.audit_log import AuditAction
from app.models.user import User
from app.audit.audit_service import record_audit_event

logger = logging.getLogger("security_failure_handling")

class PortalOutageException(Exception):
    """Raised when an external government portal is unreachable or severely degraded."""
    def __init__(self, portal_id: str, message: str, status_code: int = 503):
        super().__init__(message)
        self.portal_id = portal_id
        self.message = message
        self.status_code = status_code

class CircuitBreaker:
    """
    Circuit Breaker pattern for external statutory portals:
    States: CLOSED (normal), OPEN (tripped due to outage), HALF_OPEN (probing recovery).
    """
    def __init__(self, failure_threshold: int = 3, recovery_timeout_sec: float = 30.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout_sec
        self.state: str = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.failure_count: int = 0
        self.last_failure_time: float = 0.0

    def record_success(self):
        self.failure_count = 0
        self.state = "CLOSED"

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(f"Circuit Breaker tripped to OPEN after {self.failure_count} consecutive failures.")

    def can_execute(self) -> bool:
        if self.state == "CLOSED":
            return True
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                logger.info("Circuit Breaker probe: transitioning from OPEN to HALF_OPEN.")
                return True
            return False
        # HALF_OPEN
        return True

# Registry of circuit breakers per portal ID
CIRCUIT_BREAKERS: Dict[str, CircuitBreaker] = {}

def get_circuit_breaker(portal_id: str) -> CircuitBreaker:
    if portal_id not in CIRCUIT_BREAKERS:
        CIRCUIT_BREAKERS[portal_id] = CircuitBreaker()
    return CIRCUIT_BREAKERS[portal_id]

def handle_portal_outage(
    db: Session,
    bidder_id: int,
    portal_id: str,
    error_message: str,
    current_user: Optional[User] = None
) -> Dict[str, Any]:
    """
    Handles government portal outages gracefully:
    Instead of failing the bidder unfairly, marks their status as 'PENDING_MANUAL_REVIEW'.
    Records an immutable audit trail and triggers an incident alert.
    """
    bidder = db.query(Bidder).filter(Bidder.id == bidder_id).first()
    if not bidder:
        raise ValueError(f"Bidder with ID {bidder_id} not found.")

    old_status = bidder.composite_status
    new_status = "PENDING_MANUAL_REVIEW"
    bidder.composite_status = new_status
    bidder.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(bidder)

    # Record append-only audit trail
    record_audit_event(
        db=db,
        user=current_user,
        action=AuditAction.STATUS_CHANGE.value,
        entity_type="BIDDER",
        entity_id=str(bidder.id),
        summary=f"External statutory portal '{portal_id}' outage detected. Bidder '{bidder.company_name}' transitioned to '{new_status}' for procurement officer manual scrutiny.",
        old_values={"status": old_status},
        new_values={
            "status": new_status,
            "faulty_portal": portal_id,
            "outage_reason": error_message,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )

    logger.error(f"[Outage Alert] Portal {portal_id} failure for bidder {bidder.company_name}: {error_message}")

    return {
        "bidder_id": bidder.id,
        "company_name": bidder.company_name,
        "previous_status": old_status,
        "new_status": new_status,
        "outage_portal": portal_id,
        "action_required": "Procurement Officer must physically verify statutory documents or re-trigger verification when portal recovers.",
        "incident_timestamp": datetime.now(timezone.utc).isoformat()
    }
