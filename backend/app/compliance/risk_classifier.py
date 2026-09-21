import logging
from typing import List
from app.schemas.compliance_schema import (
    RuleEvaluationResult,
    CrossVerificationDiscrepancy,
    ScoreBreakdown,
    RiskAssessment
)

logger = logging.getLogger("compliance_risk_classifier")

class RiskClassifier:
    """
    Multi-Tier Bidder Risk Classification Engine:
    Classifies risk into LOW, MEDIUM, or HIGH based on:
    - Compliance score thresholds
    - Cross-verification discrepancy severities
    - Statutory rule failure states (e.g., blacklisting or tax suspension)
    """

    def classify_risk(
        self,
        score_breakdown: ScoreBreakdown,
        rule_results: List[RuleEvaluationResult],
        discrepancies: List[CrossVerificationDiscrepancy]
    ) -> RiskAssessment:
        score = score_breakdown.final_score

        critical_discrepancies = [d for d in discrepancies if d.severity == "CRITICAL"]
        high_discrepancies = [d for d in discrepancies if d.severity == "HIGH"]
        medium_discrepancies = [d for d in discrepancies if d.severity == "MEDIUM"]

        failed_mandatory_rules = [
            r for r in rule_results
            if r.is_mandatory and r.status == "FAILED"
        ]
        flagged_rules = [r for r in rule_results if r.status == "FLAGGED"]

        risk_factors: List[str] = []
        mitigation_actions: List[str] = []

        # ----------------------------------------------------------------------
        # Determine Risk Level & Factors
        # ----------------------------------------------------------------------
        if critical_discrepancies or failed_mandatory_rules or score < 50.0:
            risk_level = "HIGH"
            for c in critical_discrepancies:
                risk_factors.append(f"[CRITICAL] {c.description}")
            for r in failed_mandatory_rules:
                risk_factors.append(f"[RULE_FAILURE] Mandatory statutory requirement '{r.rule_name}' failed.")
            if score < 50.0:
                risk_factors.append(f"[LOW_SCORE] Overall compliance score ({score}%) is below the statutory threshold of 50%.")

            mitigation_actions.append("Issue formal Show Cause / Disqualification Notice pursuant to GFR Rule 151.")
            mitigation_actions.append("Block vendor progression to commercial / price bid opening.")

        elif high_discrepancies or flagged_rules or score < 80.0:
            risk_level = "MEDIUM"
            for h in high_discrepancies:
                risk_factors.append(f"[HIGH] {h.description}")
            for fl in flagged_rules:
                risk_factors.append(f"[OBSERVATION] {fl.rule_name}: {fl.discrepancy_notes or 'Pending verification'}")
            if score < 80.0:
                risk_factors.append(f"[MODERATE_SCORE] Compliance score ({score}%) requires officer review.")

            mitigation_actions.append("Seek official clarification through SmartBid representation window with 48h deadline.")
            mitigation_actions.append("Request notarized original statutory certificates and CA UDIN confirmation.")

        else:
            risk_level = "LOW"
            risk_factors.append("All statutory mandatory criteria fully validated against government registries.")
            risk_factors.append(f"Strong compliance rating of {score}% with zero high-severity flags.")

            mitigation_actions.append("Bidder qualified for technical bid evaluation.")
            mitigation_actions.append("Proceed to standard contract schedule terms.")

        # Compute numerical risk score [0 - 100]
        base_risk = max(0.0, 100.0 - score)
        if risk_level == "HIGH":
            risk_score = min(100.0, round(max(base_risk, 75.0) + (len(critical_discrepancies) * 5.0), 1))
        elif risk_level == "MEDIUM":
            risk_score = min(74.0, round(max(base_risk, 35.0), 1))
        else:
            risk_score = max(0.0, round(min(base_risk, 20.0), 1))

        return RiskAssessment(
            risk_level=risk_level,
            risk_score=risk_score,
            risk_factors=risk_factors,
            mitigation_actions=mitigation_actions
        )

risk_classifier = RiskClassifier()
