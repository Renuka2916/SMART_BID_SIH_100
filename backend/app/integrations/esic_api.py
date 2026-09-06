import time
from typing import Optional

from app.integrations.base import BasePortalFetcher
from app.utils.response_normalizer import (
    BidderIdentifiers,
    NormalizedPortalResponse,
    PortalStatus
)
from app.mock_data.simulated_responses import get_simulated_esic_response

class EsicFetcher(BasePortalFetcher):
    portal_id = "ESIC"
    portal_name = "ESIC - Employee State Insurance Portal"
    category = "Labor & Social Compliance"
    api_endpoint = "https://www.esic.in/api/v1/employer"

    async def fetch_data(self, identifiers: BidderIdentifiers) -> NormalizedPortalResponse:
        start_t = time.time()
        try:
            raw = get_simulated_esic_response(identifiers.esic_code, identifiers.company_name)
            latency = round((time.time() - start_t) * 1000, 2)
            e_data = raw.get("data", {})

            discrepancies = []
            if e_data.get("coverage_status") != "COVERED":
                discrepancies.append("Employer is not active under ESIC coverage.")

            if e_data.get("monthly_contribution_status") != "UP_TO_DATE":
                discrepancies.append("ESIC monthly insurance contribution remittance is in arrears.")

            is_valid = len(discrepancies) == 0 and raw.get("status") == "COMPLIANT"

            normalized = {
                "employer_code": e_data.get("employer_code"),
                "employer_name": e_data.get("employer_name"),
                "active_insured_persons": e_data.get("active_insured_persons"),
                "coverage_status": e_data.get("coverage_status"),
                "monthly_contribution_status": e_data.get("monthly_contribution_status"),
                "is_esic_compliant": is_valid
            }

            return NormalizedPortalResponse(
                portal_id=self.portal_id,
                portal_name=self.portal_name,
                category=self.category,
                status=PortalStatus.VERIFIED if is_valid else PortalStatus.FLAGGED,
                is_valid=is_valid,
                confidence_score=0.96 if is_valid else 0.60,
                discrepancies=discrepancies,
                normalized_data=normalized,
                raw_data=raw,
                latency_ms=latency
            )
        except Exception as exc:
            return self.client.build_offline_fallback(str(exc), round((time.time() - start_t) * 1000, 2))
