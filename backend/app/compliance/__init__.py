import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.models.bidder import Bidder
from app.models.tender import Tender
from app.models.document import Document
from app.models.compliance_check import ComplianceCheck, ComplianceCheckStatus
from app.models.audit_log import AuditAction
from app.models.user import User
from app.utils.encryption import decrypt_field
from app.utils.response_normalizer import BidderIdentifiers, NormalizedPortalResponse
from app.integrations.manager import portal_manager
from app.services.audit_service import record_audit_log

from app.compliance.rule_engine import rule_engine, ComplianceRuleEngine, STATUTORY_RULES_CATALOG
from app.compliance.cross_verifier import cross_verifier, CrossVerificationEngine
from app.compliance.scoring_module import scoring_module, ScoringModule
from app.compliance.risk_classifier import risk_classifier, RiskClassifier
from app.compliance.recommendation_generator import recommendation_generator, AIRecommendationGenerator
from app.schemas.compliance_schema import (
    ComplianceEvaluationReport,
    RuleEvaluationResult,
    CrossVerificationDiscrepancy,
    ScoreBreakdown,
    RiskAssessment,
    AIRecommendation
)

class ComplianceEngine:
    """
    Central Compliance & Scoring Engine Orchestrator:
    Harmonizes multi-portal statutory data, document OCR extraction,
    tender-specific checklist rules, weighted scoring, risk classification,
    and natural-language AI recommendation generation.
    """

    def __init__(self):
        self.rule_engine = rule_engine
        self.cross_verifier = cross_verifier
        self.scoring_module = scoring_module
        self.risk_classifier = risk_classifier
        self.recommendation_generator = recommendation_generator

    async def evaluate_bidder_async(
        self,
        db: Session,
        bidder_id: int,
        current_user: Optional[User] = None,
        portal_responses: Optional[Dict[str, NormalizedPortalResponse]] = None
    ) -> ComplianceEvaluationReport:
        """Asynchronous evaluation orchestrator for full statutory verification."""
        bidder = db.query(Bidder).filter(Bidder.id == bidder_id).first()
        if not bidder:
            raise ValueError(f"Bidder with ID {bidder_id} not found.")

        tender = bidder.tender
        documents = db.query(Document).filter(Document.bidder_id == bidder.id).all()

        # Decrypt sensitive identifiers for statutory validation
        pan_plaintext = decrypt_field(bidder.pan_encrypted) if bidder.pan_encrypted else bidder.pan_masked
        gstin_plaintext = decrypt_field(bidder.gstin_encrypted) if bidder.gstin_encrypted else bidder.gstin_masked
        udyam_plaintext = None
        if bidder.udyam_no_encrypted:
            udyam_plaintext = decrypt_field(bidder.udyam_no_encrypted)
        elif bidder.udyam_no_masked:
            udyam_plaintext = bidder.udyam_no_masked

        bidder_dict = {
            "id": bidder.id,
            "company_name": bidder.company_name,
            "pan": pan_plaintext,
            "gstin": gstin_plaintext,
            "udyam_no": udyam_plaintext,
            "pan_masked": bidder.pan_masked,
            "gstin_masked": bidder.gstin_masked,
            "udyam_no_masked": bidder.udyam_no_masked,
            "contact_email": bidder.contact_email,
            "contact_phone": bidder.contact_phone
        }

        tender_dict = {
            "id": tender.id if tender else 0,
            "tender_ref": tender.tender_ref if tender else "N/A",
            "title": tender.title if tender else "GeM Procurement",
            "category": tender.category if tender else "Goods",
            "estimated_value": tender.estimated_value if tender else 0.0,
            "mandatory_requirements": tender.mandatory_requirements if tender else ["GST", "PAN", "NON_BLACKLIST"]
        }

        # 1. Fetch from Government Portals if not pre-supplied
        if portal_responses is None:
            identifiers = BidderIdentifiers(
                company_name=bidder.company_name,
                pan=pan_plaintext,
                gstin=gstin_plaintext,
                udyam_no=udyam_plaintext
            )
            portal_responses = await portal_manager.fetch_all_for_bidder(identifiers)

        # 2. Evaluate Statutory & Tender-Specific Rules
        rule_results = self.rule_engine.evaluate_rules(
            bidder_data=bidder_dict,
            portal_results=portal_responses,
            tender_requirements=tender_dict["mandatory_requirements"],
            tender_meta=tender_dict
        )

        # 3. Multi-Source Field-by-Field Cross Verification
        discrepancies = self.cross_verifier.cross_verify(
            bidder_data=bidder_dict,
            portal_results=portal_responses,
            documents=documents,
            tender_metadata=tender_dict
        )

        # 4. Weighted Compliance Scoring with Discrepancy Deductions
        score_breakdown = self.scoring_module.calculate_score(
            rule_results=rule_results,
            discrepancies=discrepancies
        )

        # 5. Multi-Tier Risk Classification
        risk_assessment = self.risk_classifier.classify_risk(
            score_breakdown=score_breakdown,
            rule_results=rule_results,
            discrepancies=discrepancies
        )

        # 6. AI Natural Language Recommendation Generation
        recommendation = self.recommendation_generator.generate_recommendation(
            bidder_name=bidder.company_name,
            score_breakdown=score_breakdown,
            risk_assessment=risk_assessment,
            rule_results=rule_results,
            discrepancies=discrepancies,
            tender_meta=tender_dict
        )

        # 7. Persist Evaluation Results to DB (Bidder & ComplianceCheck entities)
        now = datetime.now(timezone.utc)
        bidder.compliance_score = score_breakdown.final_score
        
        # Composite status mapping
        if recommendation.verdict == "DISQUALIFY":
            bidder.composite_status = "NON_COMPLIANT"
        elif recommendation.verdict == "OFFICER_REVIEW":
            bidder.composite_status = "FLAGGED"
        else:
            bidder.composite_status = "COMPLIANT"

        bidder.updated_at = now

        # Sync ComplianceCheck entities
        existing_checks = {c.requirement_key: c for c in bidder.compliance_checks}
        for rr in rule_results:
            chk = existing_checks.get(rr.rule_key)
            if not chk:
                chk = ComplianceCheck(
                    bidder_id=bidder.id,
                    requirement_key=rr.rule_key,
                    portal_name=rr.portal_name
                )
                db.add(chk)
            
            chk.status = rr.status
            chk.portal_name = rr.portal_name
            chk.check_details = rr.details
            chk.discrepancy_notes = rr.discrepancy_notes
            chk.score_contribution = rr.score_awarded
            chk.verified_at = now
            chk.updated_at = now

        db.commit()
        db.refresh(bidder)

        # 8. Record Immutable Audit Log
        record_audit_log(
            db=db,
            user=current_user,
            action=AuditAction.VERIFY.value,
            entity_type="BIDDER",
            entity_id=str(bidder.id),
            summary=f"Compliance Engine evaluated '{bidder.company_name}'. Score: {bidder.compliance_score}%, Risk: {risk_assessment.risk_level}, Verdict: {recommendation.verdict}.",
            new_values={
                "compliance_score": score_breakdown.final_score,
                "risk_level": risk_assessment.risk_level,
                "verdict": recommendation.verdict,
                "discrepancies_count": len(discrepancies),
                "rules_evaluated": len(rule_results)
            }
        )

        return ComplianceEvaluationReport(
            bidder_id=bidder.id,
            company_name=bidder.company_name,
            tender_id=tender.id if tender else 0,
            tender_ref=tender.tender_ref if tender else "N/A",
            tender_title=tender.title if tender else "N/A",
            composite_status=bidder.composite_status,
            compliance_score=bidder.compliance_score,
            score_breakdown=score_breakdown,
            risk_assessment=risk_assessment,
            recommendation=recommendation,
            rules_evaluated=rule_results,
            cross_verification_discrepancies=discrepancies,
            evaluated_at=now
        )

    def evaluate_bidder_sync(
        self,
        db: Session,
        bidder_id: int,
        current_user: Optional[User] = None,
        portal_responses: Optional[Dict[str, NormalizedPortalResponse]] = None
    ) -> ComplianceEvaluationReport:
        """Synchronous wrapper for evaluate_bidder_async."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # In an active loop (e.g. within async FastAPI handler), run in executor or nest
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    return pool.submit(
                        asyncio.run,
                        self.evaluate_bidder_async(db, bidder_id, current_user, portal_responses)
                    ).result()
            else:
                return loop.run_until_complete(
                    self.evaluate_bidder_async(db, bidder_id, current_user, portal_responses)
                )
        except RuntimeError:
            return asyncio.run(
                self.evaluate_bidder_async(db, bidder_id, current_user, portal_responses)
            )

compliance_engine = ComplianceEngine()

__all__ = [
    "compliance_engine",
    "ComplianceEngine",
    "rule_engine",
    "cross_verifier",
    "scoring_module",
    "risk_classifier",
    "recommendation_generator",
    "STATUTORY_RULES_CATALOG"
]
