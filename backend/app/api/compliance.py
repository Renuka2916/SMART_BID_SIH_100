from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from app.models.user import User
from app.models.bidder import Bidder
from app.api.auth import get_current_user, require_procurement_officer
from app.compliance import compliance_engine, rule_engine
from app.schemas.compliance_schema import (
    ComplianceEvaluationReport,
    RuleEvaluationResult
)

router = APIRouter(tags=["Compliance & Scoring Engine"])

@router.get("/compliance/rules", response_model=List[Dict[str, Any]])
def list_statutory_rules(
    current_user: User = Depends(get_current_user)
):
    """
    Returns the codified catalog of statutory and tender-specific compliance rules:
    - Rule Keys: GST, PAN, NON_BLACKLIST, MAKE_IN_INDIA, OEM_AUTH, TURNOVER, etc.
    - Default weights, portal mappings, and statutory descriptions.
    """
    return rule_engine.get_rule_catalog()

@router.post("/compliance/evaluate/{bidder_id}", response_model=ComplianceEvaluationReport)
async def evaluate_bidder(
    bidder_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_procurement_officer)
):
    """
    Triggers the Full AI Compliance & Scoring Engine for a Bidder:
    1. Multi-portal parallel data fetch (GSTN, CBDT, CPPP, EPFO, MCA21, etc.).
    2. Tender-specific & statutory rule evaluation.
    3. Multi-source field-by-field cross-verification (DB vs Document OCR vs Portal).
    4. Weighted compliance scoring with discrepancy deduction penalties.
    5. Multi-tier risk classification (LOW, MEDIUM, HIGH).
    6. Natural language AI Recommendation & Executive Summary.
    7. Appends immutable audit record to AuditLog.
    """
    bidder = db.query(Bidder).filter(Bidder.id == bidder_id).first()
    if not bidder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bidder with ID {bidder_id} not found."
        )

    report = await compliance_engine.evaluate_bidder_async(
        db=db,
        bidder_id=bidder_id,
        current_user=current_user
    )
    return report

@router.get("/compliance/report/{bidder_id}", response_model=ComplianceEvaluationReport)
async def get_bidder_compliance_report(
    bidder_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves the latest comprehensive Compliance Evaluation Report for a bidder.
    If not yet evaluated, generates one dynamically.
    """
    bidder = db.query(Bidder).filter(Bidder.id == bidder_id).first()
    if not bidder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bidder with ID {bidder_id} not found."
        )

    # Run evaluation to produce complete report
    report = await compliance_engine.evaluate_bidder_async(
        db=db,
        bidder_id=bidder_id,
        current_user=current_user
    )
    return report
