from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc

from database import get_db
from app.models.tender import Tender
from app.models.user import User
from app.schemas.tender_schema import (
    TenderCreate,
    TenderUpdate,
    TenderResponse,
    TenderListResponse,
    StatutoryRequirementTemplate,
)
from app.api.auth import get_current_user, require_procurement_officer

router = APIRouter(prefix="/tenders", tags=["Tender Management"])

# Standard Predefined GeM Statutory Requirements Template Catalog
STATUTORY_REQUIREMENTS_CATALOG: List[StatutoryRequirementTemplate] = [
    StatutoryRequirementTemplate(
        key="UDYAM",
        name="Udyam / MSME Registration & Classification",
        category="MSME & Industrial",
        description="Verify valid Udyam Registration number, enterprise category (Micro/Small/Medium), and major activity via MSME portal.",
        is_recommended=True
    ),
    StatutoryRequirementTemplate(
        key="GST",
        name="GSTIN Verification & Regular Return Filing",
        category="Statutory & Taxation",
        description="Verify active GSTIN status, legal business name, tax jurisdiction, and GSTR-3B / GSTR-1 return filing recency.",
        is_recommended=True
    ),
    StatutoryRequirementTemplate(
        key="PAN",
        name="PAN Verification & Income Tax Return Compliance",
        category="Statutory & Taxation",
        description="Verify PAN validity with CBDT / Income Tax Department and submission of ITR filings for past 3 Financial Years.",
        is_recommended=True
    ),
    StatutoryRequirementTemplate(
        key="MAKE_IN_INDIA",
        name="Make in India (MII) / Local Content Compliance",
        category="Policy & Preferential",
        description="Check self-declaration or auditor certificate for Class-I (min 50%) or Class-II (min 20%) local content percentage.",
        is_recommended=True
    ),
    StatutoryRequirementTemplate(
        key="EPFO_ESIC",
        name="EPFO & ESIC Statutory Compliance",
        category="Labor & Social",
        description="Validate active establishment registration with EPFO & ESIC, employee count, and regular challan payment records.",
        is_recommended=True
    ),
    StatutoryRequirementTemplate(
        key="STARTUP_INDIA",
        name="Startup India DPIIT Recognition",
        category="Policy & Preferential",
        description="Verify entity DPIIT certificate for eligibility under public procurement turnover and prior experience exemptions.",
        is_recommended=False
    ),
    StatutoryRequirementTemplate(
        key="NSIC",
        name="NSIC Registration & Benefits",
        category="MSME & Industrial",
        description="Validate National Small Industries Corporation Single Point Registration Scheme certificate for tender fee/EMD exemptions.",
        is_recommended=False
    ),
    StatutoryRequirementTemplate(
        key="OEM_AUTH",
        name="OEM Manufacturer Authorization Form (MAF)",
        category="Technical Eligibility",
        description="Validate authentic Manufacturer Authorization Certificate with OEM verifiable contact and serial range.",
        is_recommended=True
    ),
    StatutoryRequirementTemplate(
        key="DIGILOCKER",
        name="DigiLocker Verified Statutory Credentials",
        category="Document Integrity",
        description="Ensure documents and certificates are cryptographically verifiable through the national DigiLocker repository.",
        is_recommended=True
    ),
    StatutoryRequirementTemplate(
        key="NON_BLACKLIST",
        name="Debarment & Non-Blacklisting Portal Cross-Check",
        category="Integrity & Statutory",
        description="Cross-check bidder against CPPP/GeM debarment lists, central vigilance database, and state procurement debarment rosters.",
        is_recommended=True
    ),
    StatutoryRequirementTemplate(
        key="TURNOVER",
        name="Annual Turnover & Audited Balance Sheets",
        category="Financial Eligibility",
        description="Verify Chartered Accountant (CA) certified turnover with valid UDIN (Unique Document Identification Number).",
        is_recommended=True
    ),
]

@router.get("/requirements/templates", response_model=List[StatutoryRequirementTemplate])
def get_statutory_requirements_templates():
    """Returns standard catalog of GeM statutory and compliance requirements."""
    return STATUTORY_REQUIREMENTS_CATALOG

@router.get("", response_model=TenderListResponse)
def list_tenders(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by title, ref, or department"),
    status: Optional[str] = Query(None, description="Filter by status: Draft, Published, Under Evaluation, Closed"),
    category: Optional[str] = Query(None, description="Filter by category: Goods, Services, Works"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List tenders with search, filtering, and pagination. Accessible to authenticated users."""
    query = db.query(Tender)

    if search:
        search_pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Tender.title.ilike(search_pattern),
                Tender.tender_ref.ilike(search_pattern),
                Tender.department.ilike(search_pattern)
            )
        )

    if status and status != "All":
        query = query.filter(Tender.status == status)

    if category and category != "All":
        query = query.filter(Tender.category == category)

    total = query.count()
    skip = (page - 1) * limit
    tenders = query.order_by(desc(Tender.created_at)).offset(skip).limit(limit).all()

    # Map created_by_name
    items = []
    for t in tenders:
        res = TenderResponse.model_validate(t)
        if t.created_by:
            res.created_by_name = t.created_by.full_name
        items.append(res)

    return TenderListResponse(
        total=total,
        page=page,
        limit=limit,
        items=items
    )

@router.post("", response_model=TenderResponse, status_code=status.HTTP_201_CREATED)
def create_tender(
    tender_in: TenderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_procurement_officer)
):
    """
    Create a new Tender with selected statutory requirements.
    RBAC: Restricted exclusively to Procurement Officers and Admins.
    """
    # Check if tender_ref already exists
    existing = db.query(Tender).filter(Tender.tender_ref == tender_in.tender_ref.strip()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tender with Reference ID '{tender_in.tender_ref}' already exists."
        )

    if tender_in.closing_date <= tender_in.opening_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tender closing date must be after the opening date."
        )

    tender = Tender(
        tender_ref=tender_in.tender_ref.strip(),
        title=tender_in.title.strip(),
        description=tender_in.description,
        category=tender_in.category,
        estimated_value=tender_in.estimated_value,
        department=tender_in.department,
        opening_date=tender_in.opening_date,
        closing_date=tender_in.closing_date,
        status=tender_in.status,
        mandatory_requirements=tender_in.mandatory_requirements,
        created_by_id=current_user.id
    )

    db.add(tender)
    db.commit()
    db.refresh(tender)

    res = TenderResponse.model_validate(tender)
    res.created_by_name = current_user.full_name
    return res

@router.get("/{id}", response_model=TenderResponse)
def get_tender_by_id(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get single tender details by ID."""
    tender = db.query(Tender).filter(Tender.id == id).first()
    if not tender:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tender with ID {id} not found."
        )
    
    res = TenderResponse.model_validate(tender)
    if tender.created_by:
        res.created_by_name = tender.created_by.full_name
    return res

@router.put("/{id}", response_model=TenderResponse)
def update_tender(
    id: int,
    tender_update: TenderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_procurement_officer)
):
    """
    Update tender metadata and statutory checklist.
    RBAC: Restricted exclusively to Procurement Officers and Admins.
    """
    tender = db.query(Tender).filter(Tender.id == id).first()
    if not tender:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tender with ID {id} not found."
        )

    update_data = tender_update.model_dump(exclude_unset=True)
    
    # Enforce tender lifecycle modification rules:
    # 1. Closed tenders are completely immutable.
    # 2. Published tenders are legally frozen while open to bidders. Only status transitions are permitted.
    if tender.status == "Closed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tender is Closed and cannot be modified. Concluded tenders are immutable."
        )

    if tender.status == "Published":
        disallowed_fields = [k for k in update_data.keys() if k != "status"]
        if disallowed_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Published tenders cannot be edited. Specifications and mandatory checks are legally frozen while open for bidding. Status may only be transitioned to 'Under Evaluation' or 'Closed'."
            )

    # Check date consistency if dates are updated
    new_opening = update_data.get("opening_date", tender.opening_date)
    new_closing = update_data.get("closing_date", tender.closing_date)
    if new_closing <= new_opening:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tender closing date must be after the opening date."
        )

    for field, val in update_data.items():
        setattr(tender, field, val)

    tender.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(tender)

    res = TenderResponse.model_validate(tender)
    if tender.created_by:
        res.created_by_name = tender.created_by.full_name
    return res

@router.delete("/{id}", status_code=status.HTTP_200_OK)
def delete_tender(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_procurement_officer)
):
    """
    Delete a tender.
    RBAC: Restricted exclusively to Procurement Officers and Admins.
    Lifecycle: Only 'Draft' tenders can be deleted. Published/Closed tenders must be preserved for audit.
    """
    tender = db.query(Tender).filter(Tender.id == id).first()
    if not tender:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tender with ID {id} not found."
        )

    if tender.status != "Draft":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete tender with status '{tender.status}'. Only tenders in 'Draft' status can be deleted."
        )

    db.delete(tender)
    db.commit()
    return {"message": f"Tender '{tender.tender_ref}' deleted successfully.", "id": id}
