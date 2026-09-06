import re
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.bidder import Bidder
from app.models.tender import Tender
from app.models.compliance_check import ComplianceCheck, ComplianceCheckStatus
from app.models.audit_log import AuditAction
from app.models.user import User
from app.schemas.bidder_schema import BidderCreate, BidderUpdate
from app.utils.encryption import (
    encrypt_field,
    decrypt_field,
    mask_pan,
    mask_gstin,
    mask_udyam,
)
from app.services.audit_service import record_audit_log
from app.compliance import compliance_engine

PORTAL_MAPPING: Dict[str, str] = {
    "UDYAM": "MSME_UDYAM",
    "GST": "GSTN",
    "PAN": "INCOME_TAX_CBDT",
    "MAKE_IN_INDIA": "DPIIT_MII",
    "EPFO_ESIC": "EPFO_SHRAM_SUVIDHA",
    "STARTUP_INDIA": "STARTUP_INDIA_DPIIT",
    "NSIC": "NSIC_PORTAL",
    "OEM_AUTH": "OEM_VERIFICATION",
    "DIGILOCKER": "DIGILOCKER_API",
    "NON_BLACKLIST": "CPPP_DEBARMENT",
    "TURNOVER": "MCA21_CBDT",
}

def normalize_company_name(name: str) -> str:
    """Normalizes company name by collapsing whitespace and standardizing casing."""
    cleaned = re.sub(r"\s+", " ", name.strip())
    return cleaned

def create_bidder(
    db: Session,
    tender_id: int,
    bidder_in: BidderCreate,
    current_user: Optional[User] = None
) -> Bidder:
    """
    Creates a new Bidder submission under a Tender:
    1. Validates tender exists.
    2. Validates against duplicate submissions under this tender (PAN/GSTIN match).
    3. Normalizes name.
    4. Encrypts PAN, GSTIN, and Udyam No with AES-256.
    5. Automatically initializes ComplianceCheck records for each mandatory requirement.
    6. Appends an immutable audit log entry.
    """
    tender = db.query(Tender).filter(Tender.id == tender_id).first()
    if not tender:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tender with ID {tender_id} not found."
        )

    norm_name = normalize_company_name(bidder_in.company_name)
    pan_clean = bidder_in.pan.strip().upper()
    gstin_clean = bidder_in.gstin.strip().upper()
    udyam_clean = bidder_in.udyam_no.strip().upper() if bidder_in.udyam_no else None

    # Check for duplicate bidder under same tender (PAN check)
    target_pan_masked = mask_pan(pan_clean)
    existing_candidates = db.query(Bidder).filter(
        Bidder.tender_id == tender_id,
        Bidder.pan_masked == target_pan_masked
    ).all()

    for candidate in existing_candidates:
        try:
            if decrypt_field(candidate.pan_encrypted) == pan_clean:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Bidder with PAN {target_pan_masked} has already submitted a bid for Tender '{tender.tender_ref}'."
                )
        except HTTPException:
            raise
        except Exception:
            pass

    # AES-256 Encryption
    pan_enc = encrypt_field(pan_clean)
    gstin_enc = encrypt_field(gstin_clean)
    udyam_enc = encrypt_field(udyam_clean) if udyam_clean else None

    bidder = Bidder(
        tender_id=tender_id,
        company_name=norm_name,
        pan_encrypted=pan_enc,
        pan_masked=target_pan_masked,
        gstin_encrypted=gstin_enc,
        gstin_masked=mask_gstin(gstin_clean),
        udyam_no_encrypted=udyam_enc,
        udyam_no_masked=mask_udyam(udyam_clean) if udyam_clean else None,
        contact_email=bidder_in.contact_email,
        contact_phone=bidder_in.contact_phone,
        composite_status="UNDER_REVIEW",
        compliance_score=0.0
    )
    db.add(bidder)
    db.commit()
    db.refresh(bidder)

    # Initialize ComplianceCheck entities matching Tender's mandatory requirements
    req_keys = tender.mandatory_requirements or []
    for key in req_keys:
        portal = PORTAL_MAPPING.get(key, "STATUTORY_PORTAL")
        check = ComplianceCheck(
            bidder_id=bidder.id,
            requirement_key=key,
            portal_name=portal,
            status=ComplianceCheckStatus.PENDING.value,
            check_details={"initialized_from_tender": tender.tender_ref},
            score_contribution=round(100.0 / max(len(req_keys), 1), 2)
        )
        db.add(check)

    db.commit()

    # Record Audit Log
    record_audit_log(
        db=db,
        user=current_user,
        action=AuditAction.CREATE.value,
        entity_type="BIDDER",
        entity_id=str(bidder.id),
        summary=f"Created Bidder '{bidder.company_name}' under Tender '{tender.tender_ref}' with {len(req_keys)} mandatory compliance checks.",
        new_values={
            "bidder_id": bidder.id,
            "company_name": bidder.company_name,
            "pan_masked": bidder.pan_masked,
            "gstin_masked": bidder.gstin_masked,
            "tender_id": tender.id,
            "checks_initialized": len(req_keys)
        }
    )

    return bidder

def get_bidder_with_pii(
    db: Session,
    bidder_id: int,
    decrypt_pii: bool = True
) -> Dict[str, Any]:
    """Retrieves a single bidder with optional on-the-fly AES-256 decryption."""
    bidder = db.query(Bidder).filter(Bidder.id == bidder_id).first()
    if not bidder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bidder with ID {bidder_id} not found."
        )

    data = {
        "id": bidder.id,
        "tender_id": bidder.tender_id,
        "tender_ref": bidder.tender.tender_ref if bidder.tender else None,
        "tender_title": bidder.tender.title if bidder.tender else None,
        "company_name": bidder.company_name,
        "pan_masked": bidder.pan_masked,
        "gstin_masked": bidder.gstin_masked,
        "udyam_no_masked": bidder.udyam_no_masked,
        "contact_email": bidder.contact_email,
        "contact_phone": bidder.contact_phone,
        "composite_status": bidder.composite_status,
        "compliance_score": bidder.compliance_score,
        "documents_count": len(bidder.documents),
        "checks_count": len(bidder.compliance_checks),
        "created_at": bidder.created_at,
        "updated_at": bidder.updated_at,
        "pan": None,
        "gstin": None,
        "udyam_no": None
    }

    if decrypt_pii:
        try:
            data["pan"] = decrypt_field(bidder.pan_encrypted)
            data["gstin"] = decrypt_field(bidder.gstin_encrypted)
            if bidder.udyam_no_encrypted:
                data["udyam_no"] = decrypt_field(bidder.udyam_no_encrypted)
        except Exception as e:
            data["pan"] = bidder.pan_masked
            data["gstin"] = bidder.gstin_masked

    return data

def list_all_bidders(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    decrypt_pii: bool = False
) -> Tuple[int, List[Dict[str, Any]]]:
    """Lists all bidders across all tenders with attached tender metadata."""
    query = db.query(Bidder)
    total = query.count()
    bidders = query.order_by(Bidder.created_at.desc()).offset(skip).limit(limit).all()

    items = []
    for b in bidders:
        item = {
            "id": b.id,
            "tender_id": b.tender_id,
            "tender_ref": b.tender.tender_ref if b.tender else None,
            "tender_title": b.tender.title if b.tender else None,
            "company_name": b.company_name,
            "pan_masked": b.pan_masked,
            "gstin_masked": b.gstin_masked,
            "udyam_no_masked": b.udyam_no_masked,
            "contact_email": b.contact_email,
            "contact_phone": b.contact_phone,
            "composite_status": b.composite_status,
            "compliance_score": b.compliance_score,
            "documents_count": len(b.documents),
            "checks_count": len(b.compliance_checks),
            "created_at": b.created_at,
            "updated_at": b.updated_at,
            "pan": None,
            "gstin": None,
            "udyam_no": None
        }
        if decrypt_pii:
            try:
                item["pan"] = decrypt_field(b.pan_encrypted)
                item["gstin"] = decrypt_field(b.gstin_encrypted)
                if b.udyam_no_encrypted:
                    item["udyam_no"] = decrypt_field(b.udyam_no_encrypted)
            except Exception:
                pass
        items.append(item)

    return total, items

def list_bidders_for_tender(
    db: Session,
    tender_id: int,
    skip: int = 0,
    limit: int = 50,
    decrypt_pii: bool = False
) -> Tuple[int, List[Dict[str, Any]]]:
    """Lists bidders for a specific tender."""
    query = db.query(Bidder).filter(Bidder.tender_id == tender_id)
    total = query.count()
    bidders = query.offset(skip).limit(limit).all()

    items = []
    for b in bidders:
        item = {
            "id": b.id,
            "tender_id": b.tender_id,
            "tender_ref": b.tender.tender_ref if b.tender else None,
            "tender_title": b.tender.title if b.tender else None,
            "company_name": b.company_name,
            "pan_masked": b.pan_masked,
            "gstin_masked": b.gstin_masked,
            "udyam_no_masked": b.udyam_no_masked,
            "contact_email": b.contact_email,
            "contact_phone": b.contact_phone,
            "composite_status": b.composite_status,
            "compliance_score": b.compliance_score,
            "documents_count": len(b.documents),
            "checks_count": len(b.compliance_checks),
            "created_at": b.created_at,
            "updated_at": b.updated_at,
            "pan": None,
            "gstin": None,
            "udyam_no": None
        }
        if decrypt_pii:
            try:
                item["pan"] = decrypt_field(b.pan_encrypted)
                item["gstin"] = decrypt_field(b.gstin_encrypted)
                if b.udyam_no_encrypted:
                    item["udyam_no"] = decrypt_field(b.udyam_no_encrypted)
            except Exception:
                pass
        items.append(item)

    return total, items

def get_bidder_compliance_checks(db: Session, bidder_id: int) -> List[ComplianceCheck]:
    """Returns all compliance check entities for a bidder."""
    return db.query(ComplianceCheck).filter(ComplianceCheck.bidder_id == bidder_id).all()

def evaluate_bidder_compliance(
    db: Session,
    bidder_id: int,
    current_user: Optional[User] = None
) -> Tuple[Bidder, List[ComplianceCheck]]:
    """
    Executes the automated AI Verification Engine across all statutory compliance checks for a bidder
    by delegating to the unified Compliance & Scoring Engine:
    1. Multi-portal parallel data fetch & normalization.
    2. Tender-specific checklist rule evaluation.
    3. Multi-source cross-verification (DB vs Document OCR vs Govt Portal).
    4. Weighted compliance scoring with discrepancy penalties.
    5. Multi-tier risk classification (LOW, MEDIUM, HIGH).
    6. Natural language AI recommendations.
    7. Immutable audit log registration.
    """
    bidder = db.query(Bidder).filter(Bidder.id == bidder_id).first()
    if not bidder:
        raise HTTPException(status_code=404, detail=f"Bidder with ID {bidder_id} not found.")

    compliance_engine.evaluate_bidder_sync(
        db=db,
        bidder_id=bidder_id,
        current_user=current_user
    )

    db.refresh(bidder)
    checks = db.query(ComplianceCheck).filter(ComplianceCheck.bidder_id == bidder_id).all()
    return bidder, checks

def record_officer_decision(
    db: Session,
    bidder_id: int,
    decision: str,
    notes: Optional[str] = None,
    current_user: Optional[User] = None
) -> Bidder:
    """Records the Procurement Officer's final qualification/disqualification decision."""
    bidder = db.query(Bidder).filter(Bidder.id == bidder_id).first()
    if not bidder:
        raise HTTPException(status_code=404, detail=f"Bidder with ID {bidder_id} not found.")

    old_status = bidder.composite_status
    bidder.composite_status = decision  # QUALIFIED or DISQUALIFIED
    bidder.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(bidder)

    record_audit_log(
        db=db,
        user=current_user,
        action=AuditAction.DECISION_OVERRIDE.value,
        entity_type="BIDDER",
        entity_id=str(bidder.id),
        summary=f"Procurement Officer decided: {decision} for Bidder '{bidder.company_name}'. Notes: {notes or 'None'}",
        old_values={"status": old_status},
        new_values={"status": decision, "notes": notes}
    )

    return bidder

def update_bidder(
    db: Session,
    bidder_id: int,
    bidder_update: BidderUpdate,
    current_user: Optional[User] = None
) -> Bidder:
    """Updates non-PII attributes with audit logging."""
    bidder = db.query(Bidder).filter(Bidder.id == bidder_id).first()
    if not bidder:
        raise HTTPException(status_code=404, detail=f"Bidder with ID {bidder_id} not found.")

    old_vals = {
        "company_name": bidder.company_name,
        "contact_email": bidder.contact_email,
        "composite_status": bidder.composite_status,
        "compliance_score": bidder.compliance_score,
    }

    update_dict = bidder_update.model_dump(exclude_unset=True)
    if "company_name" in update_dict and update_dict["company_name"]:
        update_dict["company_name"] = normalize_company_name(update_dict["company_name"])

    for k, v in update_dict.items():
        setattr(bidder, k, v)

    db.commit()
    db.refresh(bidder)

    new_vals = {
        "company_name": bidder.company_name,
        "contact_email": bidder.contact_email,
        "composite_status": bidder.composite_status,
        "compliance_score": bidder.compliance_score,
    }

    record_audit_log(
        db=db,
        user=current_user,
        action=AuditAction.UPDATE.value,
        entity_type="BIDDER",
        entity_id=str(bidder.id),
        summary=f"Updated Bidder '{bidder.company_name}' details.",
        old_values=old_vals,
        new_values=new_vals
    )

    return bidder

def delete_bidder(
    db: Session,
    bidder_id: int,
    current_user: Optional[User] = None
) -> Dict[str, Any]:
    """Deletes bidder, cascading to documents and compliance checks, with audit log."""
    bidder = db.query(Bidder).filter(Bidder.id == bidder_id).first()
    if not bidder:
        raise HTTPException(status_code=404, detail=f"Bidder with ID {bidder_id} not found.")

    company_name = bidder.company_name
    tender_id = bidder.tender_id

    db.delete(bidder)
    db.commit()

    record_audit_log(
        db=db,
        user=current_user,
        action=AuditAction.DELETE.value,
        entity_type="BIDDER",
        entity_id=str(bidder_id),
        summary=f"Deleted Bidder '{company_name}' from Tender ID {tender_id}."
    )

    return {"message": f"Bidder '{company_name}' successfully removed.", "id": bidder_id}
