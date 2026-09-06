import logging
from typing import List, Dict, Any
from app.schemas.compliance_schema import (
    RuleEvaluationResult,
    CrossVerificationDiscrepancy,
    ScoreBreakdown
)

logger = logging.getLogger("compliance_scoring_module")

class ScoringModule:
    """
    Weighted Compliance Scoring Engine:
    - Aggregates dynamic rule scores based on tender requirements.
    - Applies calibrated penalties for cross-verification discrepancies.
    - Computes category-wise performance distributions.
    - Bounds final score strictly within [0.0, 100.0].
    """

    PENALTY_WEIGHTS = {
        "CRITICAL": 30.0,
        "HIGH": 15.0,
        "MEDIUM": 5.0,
        "LOW": 2.0
    }

    def calculate_score(
        self,
        rule_results: List[RuleEvaluationResult],
        discrepancies: List[CrossVerificationDiscrepancy]
    ) -> ScoreBreakdown:
        if not rule_results:
            return ScoreBreakdown(
                raw_score=0.0,
                penalties=0.0,
                final_score=0.0,
                category_scores={}
            )

        # 1. Sum raw score awarded across evaluated rules
        raw_score = sum(r.score_awarded for r in rule_results)
        raw_score = round(min(100.0, raw_score), 2)

        # 2. Calculate category breakdown
        category_totals: Dict[str, float] = {}
        category_max: Dict[str, float] = {}

        for r in rule_results:
            cat = r.category or "General"
            category_totals[cat] = category_totals.get(cat, 0.0) + r.score_awarded
            category_max[cat] = category_max.get(cat, 0.0) + r.weight

        category_scores: Dict[str, float] = {}
        for cat, earned in category_totals.items():
            max_w = category_max.get(cat, 1.0) or 1.0
            pct = round((earned / max_w) * 100.0, 1)
            category_scores[cat] = pct

        # 3. Calculate discrepancy penalties
        total_penalties = 0.0
        for disc in discrepancies:
            sev = disc.severity.upper()
            total_penalties += self.PENALTY_WEIGHTS.get(sev, 2.0)

        # 4. Final score computation bounded between 0.0 and 100.0
        final_score = max(0.0, round(raw_score - total_penalties, 1))

        return ScoreBreakdown(
            raw_score=raw_score,
            penalties=round(total_penalties, 1),
            final_score=final_score,
            category_scores=category_scores
        )

scoring_module = ScoringModule()
