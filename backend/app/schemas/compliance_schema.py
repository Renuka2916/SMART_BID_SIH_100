from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict, Field
from app.models.compliance_check import ComplianceCheckStatus

class ComplianceCheckBase(BaseModel):
    requirement_key: str = Field(..., description="Requirement identifier, e.g. UDYAM, GST, PAN")
    portal_name: str = Field(..., description="Target portal, e.g. GSTN, MSME_UDYAM, EPFO")

class ComplianceCheckCreate(ComplianceCheckBase):
    status: ComplianceCheckStatus = ComplianceCheckStatus.PENDING
    check_details: Optional[Dict[str, Any]] = None
    discrepancy_notes: Optional[str] = None
    score_contribution: float = 0.0

class ComplianceCheckUpdate(BaseModel):
    status: ComplianceCheckStatus
    check_details: Optional[Dict[str, Any]] = None
    discrepancy_notes: Optional[str] = None
    score_contribution: Optional[float] = None
    verified_at: Optional[datetime] = None

class ComplianceCheckResponse(ComplianceCheckBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    bidder_id: int
    status: str
    check_details: Dict[str, Any] = {}
    discrepancy_notes: Optional[str] = None
    score_contribution: float
    verified_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

class ComplianceCheckListResponse(BaseModel):
    total: int
    items: List[ComplianceCheckResponse]


# ==============================================================================
# Compliance & Scoring Engine Output Schemas
# ==============================================================================

class CrossVerificationDiscrepancy(BaseModel):
    field_name: str = Field(..., description="Identifier or statutory field evaluated, e.g. PAN, GSTIN, LEGAL_NAME")
    severity: str = Field(..., description="CRITICAL, HIGH, MEDIUM, LOW")
    source_a: str = Field(..., description="Origin and data of primary source, e.g. 'Bidder Record: AAPCL1234K'")
    source_b: str = Field(..., description="Origin and data of secondary source, e.g. 'Uploaded PDF OCR: BBPLC9876Z'")
    description: str = Field(..., description="Natural language explanation of discrepancy")
    disqualification_ground: bool = Field(default=False, description="Whether this triggers statutory disqualification")

class RuleEvaluationResult(BaseModel):
    rule_key: str = Field(..., description="Statutory key code, e.g. GST, PAN, NON_BLACKLIST")
    rule_name: str = Field(..., description="Human-readable title")
    portal_name: str = Field(..., description="Associated government portal adapter")
    category: str = Field(..., description="Taxation, Identity, Financial, Technical, Preferential")
    status: str = Field(..., description="VERIFIED, FLAGGED, FAILED, EXEMPTED")
    weight: float = Field(..., description="Allocated weight percentage")
    score_awarded: float = Field(..., description="Final score contribution awarded")
    is_mandatory: bool = Field(default=True, description="Whether this is mandatory under the tender")
    details: Dict[str, Any] = Field(default_factory=dict, description="Normalized verification evidence")
    discrepancy_notes: Optional[str] = Field(default=None, description="Discrepancy note if flagged")

class ScoreBreakdown(BaseModel):
    raw_score: float = Field(..., description="Gross points earned before penalties")
    penalties: float = Field(default=0.0, description="Deductions from discrepancies")
    final_score: float = Field(..., description="Final net compliance score [0 - 100]")
    category_scores: Dict[str, float] = Field(default_factory=dict, description="Score grouped by statutory category")

class RiskAssessment(BaseModel):
    risk_level: str = Field(..., description="LOW, MEDIUM, HIGH")
    risk_score: float = Field(..., description="Risk score [0 - 100] where 100 is maximum risk")
    risk_factors: List[str] = Field(default_factory=list, description="Identified risk markers")
    mitigation_actions: List[str] = Field(default_factory=list, description="Recommended officer mitigation actions")

class AIRecommendation(BaseModel):
    verdict: str = Field(..., description="QUALIFY, OFFICER_REVIEW, DISQUALIFY")
    headline: str = Field(..., description="Executive advisory headline")
    summary: str = Field(..., description="Natural language justification")
    disqualification_grounds: List[str] = Field(default_factory=list, description="Statutory grounds for disqualification")
    policy_benefits: List[str] = Field(default_factory=list, description="Applicable procurement exemptions or preferences")
    next_actions: List[str] = Field(default_factory=list, description="Action items for Procurement Officer prior to award")

class ComplianceEvaluationReport(BaseModel):
    bidder_id: int
    company_name: str
    tender_id: int
    tender_ref: str
    tender_title: str
    composite_status: str
    compliance_score: float
    score_breakdown: ScoreBreakdown
    risk_assessment: RiskAssessment
    recommendation: AIRecommendation
    rules_evaluated: List[RuleEvaluationResult]
    cross_verification_discrepancies: List[CrossVerificationDiscrepancy]
    evaluated_at: datetime
