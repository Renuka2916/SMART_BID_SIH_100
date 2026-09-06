from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from app.models.user import User
from app.schemas.bidder_schema import (
    BidderCreate,
    BidderUpdate,
    BidderResponse,
    BidderListResponse
)
from app.schemas.compliance_schema import (
    ComplianceCheckResponse,
    ComplianceCheckListResponse
)
from app.api.auth import get_current_user, require_procurement_officer
from app.services.bidder_service import (
    create_bidder,
    get_bidder_with_pii,
    list_all_bidders,
    list_bidders_for_tender,
    get_bidder_compliance_checks,
    evaluate_bidder_compliance,
    record_officer_decision,
    update_bidder,
    delete_bidder
)

from app.workflow.decision_controller import (
    enforce_officer_qualification_decision,
    DecisionSubmissionPayload
)

router = APIRouter(tags=["Bidder Management"])

class OfficerDecisionRequest(BaseModel):
    decision: str  # QUALIFIED or DISQUALIFIED
    notes: Optional[str] = None
    remarks: Optional[str] = None
    pinned_evidence: Optional[List[Dict[str, Any]]] = None

@router.get("/bidders", response_model=BidderListResponse)
def get_all_bidders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lists all bidders across all tenders for centralized review."""
    is_officer = current_user.role.name in ["Procurement Officer", "Admin"]
    total, items = list_all_bidders(db, skip=skip, limit=limit, decrypt_pii=is_officer)
    return BidderListResponse(total=total, items=items)

@router.post("/tenders/{tender_id}/bidders", response_model=BidderResponse, status_code=status.HTTP_201_CREATED)
def submit_bidder_application(
    tender_id: int,
    bidder_in: BidderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submits a new bidder application for a specific tender:
    - Normalizes entity name
    - Encrypts PAN, GSTIN, Udyam No with AES-256
    - Prevents duplicate submissions under the same tender
    - Automatically sets up ComplianceChecks matching the tender's mandatory requirements
    - Records immutable audit log
    """
    bidder = create_bidder(db, tender_id, bidder_in, current_user)
    return get_bidder_with_pii(db, bidder.id, decrypt_pii=True)

@router.get("/tenders/{tender_id}/bidders", response_model=BidderListResponse)
def get_tender_bidders(
    tender_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lists all bidders who submitted bids for a specific tender."""
    is_officer = current_user.role.name in ["Procurement Officer", "Admin"]
    total, items = list_bidders_for_tender(db, tender_id, skip=skip, limit=limit, decrypt_pii=is_officer)
    return BidderListResponse(total=total, items=items)

@router.get("/bidders/{id}", response_model=BidderResponse)
def get_bidder_details(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves full bidder profile. Decrypts PII only for authorized Procurement Officers."""
    is_officer = current_user.role.name in ["Procurement Officer", "Admin"]
    data = get_bidder_with_pii(db, id, decrypt_pii=is_officer)
    return data

@router.get("/bidders/{id}/compliance-checks", response_model=ComplianceCheckListResponse)
def get_compliance_checks(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves all statutory compliance checks associated with a bidder."""
    checks = get_bidder_compliance_checks(db, id)
    return ComplianceCheckListResponse(total=len(checks), items=checks)

@router.post("/bidders/{id}/evaluate", response_model=BidderResponse)
def trigger_ai_compliance_evaluation(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Executes the AI Verification Engine for the specified bidder:
    - Queries connected government portal simulations (GSTN, MSME, CBDT, etc.)
    - Computes overall statutory compliance score & risk rating
    - Updates bidder status and appends an audit log
    """
    bidder, _ = evaluate_bidder_compliance(db, id, current_user)
    is_officer = current_user.role.name in ["Procurement Officer", "Admin"]
    return get_bidder_with_pii(db, bidder.id, decrypt_pii=is_officer)

@router.post("/bidders/{id}/decision", response_model=BidderResponse)
def submit_officer_decision(
    id: int,
    body: OfficerDecisionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_procurement_officer)
):
    """
    Records the Procurement Officer's final qualification/disqualification decision.
    Enforces AI Safety Gate, substantive remarks validation, and immutable audit logging.
    """
    raw_remarks = body.remarks or body.notes or "Procurement officer formal determination recorded."
    if len(raw_remarks.strip()) < 15:
        raw_remarks = raw_remarks.strip() + " - verified under GFR Rule 173."
    
    payload = DecisionSubmissionPayload(
        decision=body.decision,
        remarks=raw_remarks,
        pinned_evidence=body.pinned_evidence or []
    )
    bidder = enforce_officer_qualification_decision(db, id, payload, current_user)
    return get_bidder_with_pii(db, bidder.id, decrypt_pii=True)

@router.put("/bidders/{id}", response_model=BidderResponse)
def modify_bidder(
    id: int,
    bidder_update: BidderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_procurement_officer)
):
    """Updates bidder metadata and status. Restricted to Procurement Officers."""
    update_bidder(db, id, bidder_update, current_user)
    return get_bidder_with_pii(db, id, decrypt_pii=True)

@router.delete("/bidders/{id}")
def remove_bidder(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_procurement_officer)
):
    """Deletes a bidder and associated documents/compliance records. Restricted to Procurement Officers."""
    return delete_bidder(db, id, current_user)
