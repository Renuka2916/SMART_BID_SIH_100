import logging
from typing import List, Dict, Any
from app.schemas.compliance_schema import (
    RuleEvaluationResult,
    CrossVerificationDiscrepancy,
    ScoreBreakdown,
    RiskAssessment,
    AIRecommendation
)

logger = logging.getLogger("compliance_recommendation_generator")

class AIRecommendationGenerator:
    """
    AI Executive Summary & Recommendation Engine:
    Synthesizes rule outputs, discrepancy findings, and risk scores into
    actionable natural language advisories for SmartBid Procurement Officers.
    """

    def generate_recommendation(
        self,
        bidder_name: str,
        score_breakdown: ScoreBreakdown,
        risk_assessment: RiskAssessment,
        rule_results: List[RuleEvaluationResult],
        discrepancies: List[CrossVerificationDiscrepancy],
        tender_meta: Dict[str, Any]
    ) -> AIRecommendation:
        score = score_breakdown.final_score
        risk_level = risk_assessment.risk_level

        has_disqualifying_ground = any(d.disqualification_ground for d in discrepancies)
        failed_mandatory = [r for r in rule_results if r.is_mandatory and r.status == "FAILED"]

        disqualification_grounds: List[str] = []
        policy_benefits: List[str] = []
        next_actions: List[str] = []

        # ----------------------------------------------------------------------
        # Check Preferential Policies (MSME, Startup India, Make in India)
        # ----------------------------------------------------------------------
        for r in rule_results:
            if r.rule_key == "UDYAM" and r.status == "VERIFIED":
                policy_benefits.append(
                    "Eligible for 25% MSE Purchase Preference and full EMD exemption under Public Procurement Policy (MSEs) Order 2012."
                )
            elif r.rule_key == "STARTUP_INDIA" and r.status == "VERIFIED":
                policy_benefits.append(
                    "Eligible for DPIIT Startup relaxation on prior turnover and past experience criteria (GFR Rule 173(i))."
                )
            elif r.rule_key == "MAKE_IN_INDIA" and r.status == "VERIFIED":
                cls = r.details.get("classification", "Class-I Local Supplier")
                policy_benefits.append(
                    f"Classified as {cls}; eligible for purchase preference in Goods procurement."
                )

        # ----------------------------------------------------------------------
        # Determine Verdict & Summaries
        # ----------------------------------------------------------------------
        if risk_level == "HIGH" or has_disqualifying_ground or len(failed_mandatory) > 0:
            verdict = "DISQUALIFY"
            headline = "RECOMMENDATION: DISQUALIFY BIDDER - Critical Statutory Non-Compliance"

            for d in discrepancies:
                if d.severity == "CRITICAL" or d.disqualification_ground:
                    disqualification_grounds.append(f"{d.field_name}: {d.description}")
            for fm in failed_mandatory:
                disqualification_grounds.append(f"Statutory Failure: Mandatory requirement '{fm.rule_name}' could not be verified.")

            summary = (
                f"Automated evaluation across statutory registries indicates that '{bidder_name}' does not meet "
                f"the mandatory legal criteria for this tender (Compliance Score: {score}%, Risk: HIGH). "
                f"Disqualifying issues include {len(disqualification_grounds)} statutory violations. "
                "Participation is legally prohibited under Central Public Procurement guidelines."
            )

            next_actions = [
                "Issue formal technical disqualification record on the SmartBid portal with reference to statutory findings.",
                "Exclude bidder from commercial bid opening.",
                "Archive immutable audit verification record for CVO / Vigilance inspection."
            ]

        elif risk_level == "MEDIUM" or score < 80.0:
            verdict = "OFFICER_REVIEW"
            headline = "RECOMMENDATION: PROCUREMENT OFFICER REVIEW REQUIRED - Moderate Observations"

            summary = (
                f"Bidder '{bidder_name}' meets essential baseline criteria with a compliance score of {score}%, "
                "but has triggered moderate observations or document discrepancies. "
                "Procurement Officer evaluation is recommended before advancing to commercial evaluation."
            )

            next_actions = [
                "Request clarification or updated documentation via the SmartBid Representation Window with a 48-hour deadline.",
                "Review flagged cross-verification discrepancies against physical / original documents.",
                "Verify CA UDIN authenticity on the ICAI portal if financial turnover is in dispute."
            ]

        else:
            verdict = "QUALIFY"
            headline = "RECOMMENDATION: QUALIFY BIDDER - Statutory Compliance Verified"

            summary = (
                f"Bidder '{bidder_name}' demonstrates robust statutory compliance across all mandatory government registries "
                f"with an overall compliance score of {score}% and LOW risk profile. "
                "No adverse vigilance records, blacklisting matches, or tax irregularities were detected."
            )

            next_actions = [
                "Approve bidder for technical bid evaluation.",
                "Verify preferential purchase policy applicability during final commercial bid evaluation.",
                "Proceed with contract milestone scheduling."
            ]

        return AIRecommendation(
            verdict=verdict,
            headline=headline,
            summary=summary,
            disqualification_grounds=disqualification_grounds,
            policy_benefits=policy_benefits,
            next_actions=next_actions
        )

recommendation_generator = AIRecommendationGenerator()
