from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from app.models.user import User
from app.models.bidder import Bidder
from app.api.auth import get_current_user
from app.integrations.manager import portal_manager
from app.utils.response_normalizer import BidderIdentifiers, NormalizedPortalResponse
from app.utils.encryption import decrypt_field
from app.services.audit_service import record_audit_log

router = APIRouter(prefix="/integrations", tags=["Multi-Portal Integrations"])

@router.get("/portals")
def list_registered_portals(current_user: User = Depends(get_current_user)):
    """
    Returns the catalog of all 15+ integrated statutory government verification portals.
    Shows connection status, gateway mode, and adapter parameters.
    """
    portals = portal_manager.get_all_registered_portals()
    return {
        "total_portals": len(portals),
        "status": "HEALTHY",
        "items": portals
    }

@router.post("/fetch/{portal_id}", response_model=NormalizedPortalResponse)
async def fetch_single_portal_data(
    portal_id: str,
    identifiers: BidderIdentifiers,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Directly fetches and normalizes verification data from a specific statutory portal adapter.
    """
    fetcher = portal_manager.get_fetcher(portal_id)
    if not fetcher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portal adapter '{portal_id}' not found."
        )

    res = await portal_manager.fetch_single_portal(portal_id, identifiers)
    
    # Audit log entry
    record_audit_log(
        db=db,
        user=current_user,
        action="INTEGRATION_FETCH",
        entity_type="PORTAL_INTEGRATION",
        entity_id=portal_id,
        summary=f"Fetched data from {fetcher.portal_name} for '{identifiers.company_name}' (Status: {res.status.value})",
        new_values={"portal_id": portal_id, "status": res.status.value, "is_valid": res.is_valid, "latency_ms": res.latency_ms}
    )

    return res

@router.post("/verify-bidder/{bidder_id}")
async def verify_bidder_across_all_portals(
    bidder_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Executes parallel multi-portal verification across all 15 government portals for a stored bidder.
    Decrypted PII is used in-memory for official API querying.
    """
    bidder = db.query(Bidder).filter(Bidder.id == bidder_id).first()
    if not bidder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bidder with ID {bidder_id} not found."
        )

    # Decrypt identifiers in-memory
    pan = None
    gstin = None
    udyam_no = None
    try:
        pan = decrypt_field(bidder.pan_encrypted)
        gstin = decrypt_field(bidder.gstin_encrypted)
        if bidder.udyam_no_encrypted:
            udyam_no = decrypt_field(bidder.udyam_no_encrypted)
    except Exception:
        pan = bidder.pan_masked
        gstin = bidder.gstin_masked

    identifiers = BidderIdentifiers(
        company_name=bidder.company_name,
        pan=pan,
        gstin=gstin,
        udyam_no=udyam_no,
        contact_email=bidder.contact_email,
        contact_phone=bidder.contact_phone
    )

    # Parallel asynchronous dispatch to all 15 portals
    results = await portal_manager.fetch_all_for_bidder(identifiers)

    # Compute aggregate compliance
    score, composite_status, discrepancies = portal_manager.aggregate_compliance(results)

    # Record audit log
    record_audit_log(
        db=db,
        user=current_user,
        action="MULTI_PORTAL_VERIFICATION",
        entity_type="BIDDER",
        entity_id=str(bidder.id),
        summary=f"Executed 15-portal verification for '{bidder.company_name}' - Score: {score}% ({composite_status})",
        new_values={
            "portals_checked": len(results),
            "score": score,
            "status": composite_status,
            "discrepancies_count": len(discrepancies)
        }
    )

    # Convert results to serializable dict
    serialized_results = {k: v.model_dump() for k, v in results.items()}

    return {
        "bidder_id": bidder.id,
        "company_name": bidder.company_name,
        "compliance_score": score,
        "composite_status": composite_status,
        "total_portals_checked": len(results),
        "discrepancies": discrepancies,
        "portal_results": serialized_results
    }
