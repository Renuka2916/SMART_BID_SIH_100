import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field, field_validator
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.bidder import Bidder
from app.models.tender import Tender
from app.models.user import User
from app.models.audit_log import AuditAction
from app.audit.audit_service import record_audit_event

logger = logging.getLogger("workflow_decision_controller")

class DecisionSubmissionPayload(BaseModel):
    decision: str = Field(..., description="Formal determination: QUALIFIED or DISQUALIFIED")
    remarks: str = Field(..., description="Mandatory substantive officer evaluation notes (min 15 characters)", min_length=15)
    pinned_evidence: Optional[List[Dict[str, Any]]] = Field(default=[], description="Pinned discrepancies and statutory findings attached to decision")

    @field_validator("decision")
    def validate_decision_enum(cls, v: str) -> str:
        clean = v.strip().upper()
        if clean not in ["QUALIFIED", "DISQUALIFIED"]:
            raise ValueError("Decision must be either 'QUALIFIED' or 'DISQUALIFIED'.")
        return clean

    @field_validator("remarks")
    def validate_remarks_not_empty(cls, v: str) -> str:
        if len(v.strip()) < 15:
            raise ValueError("Remarks must contain at least 15 characters of substantive procurement justification.")
        return v.strip()

def validate_ai_safety_gate(user: Optional[User]) -> None:
    """
    AI Safety Gate:
    Under GFR Rule 173 and GeM Procurement Guidelines, AI recommendations are strictly advisory.
    No automated algorithm or non-authenticated background process may qualify or disqualify a bidder.
    A certified human Procurement Officer or Admin must review and sign the determination.
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="AI Safety Violation: Automated qualification without an authenticated human session is prohibited."
        )

    user_role = getattr(user.role, "name", "")
    if user_role not in ["Procurement Officer", "Admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="AI Safety Violation: Only authorized human Procurement Officers or Admins may execute qualification determinations."
        )

def enforce_officer_qualification_decision(
    db: Session,
    bidder_id: int,
    payload: DecisionSubmissionPayload,
    current_user: User
) -> Bidder:
    """
    Enforces the final qualification/disqualification workflow:
    1. Validates human-in-the-loop safety gate.
    2. Validates tender lifecycle state (cannot modify decisions on Closed tenders).
    3. Validates mandatory substantive officer remarks.
    4. Updates bidder composite status.
    5. Records an immutable append-only audit log entry with pinned evidence docket.
    """
    # 1. AI Safety Gate Check
    validate_ai_safety_gate(current_user)

    # 2. Retrieve Bidder & Tender
    bidder = db.query(Bidder).filter(Bidder.id == bidder_id).first()
    if not bidder:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Bidder with ID {bidder_id} not found.")

    tender = bidder.tender
    if tender and tender.status == "Closed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tender '{tender.tender_ref}' is Closed and archived. Bidders in concluded tenders cannot be modified."
        )

    # 3. Apply State Transition
    old_status = bidder.composite_status
    decision = payload.decision
    remarks = payload.remarks
    pinned = payload.pinned_evidence or []

    bidder.composite_status = decision
    bidder.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(bidder)

    # 4. Record Immutable Audit Log
    record_audit_event(
        db=db,
        user=current_user,
        action=AuditAction.DECISION_OVERRIDE.value,
        entity_type="BIDDER",
        entity_id=str(bidder.id),
        summary=f"Procurement Officer '{current_user.email}' signed formal determination: {decision} for Bidder '{bidder.company_name}'. Remarks: {remarks}",
        old_values={"status": old_status},
        new_values={
            "status": decision,
            "remarks": remarks,
            "pinned_evidence_count": len(pinned),
            "pinned_evidence": pinned,
            "compliance_score_at_decision": bidder.compliance_score,
            "signing_timestamp": datetime.now(timezone.utc).isoformat()
        }
    )

    logger.info(
        f"[Decision Logged] Bidder {bidder.id} ({bidder.company_name}) set to {decision} by {current_user.email}."
    )

    return bidder
