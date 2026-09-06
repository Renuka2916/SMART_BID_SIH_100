import time
from typing import Optional

from app.integrations.base import BasePortalFetcher
from app.utils.response_normalizer import (
    BidderIdentifiers,
    NormalizedPortalResponse,
    PortalStatus
)
from app.mock_data.simulated_responses import get_simulated_startup_india_response

class StartupIndiaFetcher(BasePortalFetcher):
    portal_id = "STARTUP_INDIA"
    portal_name = "Startup India - DPIIT Recognition Registry"
    category = "Policy & Preferential Eligibility"
    api_endpoint = "https://www.startupindia.gov.in/api/v1/recognition"

    async def fetch_data(self, identifiers: BidderIdentifiers) -> NormalizedPortalResponse:
        start_t = time.time()
        try:
            raw = get_simulated_startup_india_response(identifiers.startup_dipp_no, identifiers.company_name)
            latency = round((time.time() - start_t) * 1000, 2)
            s_data = raw.get("data", {})

            is_recognized = raw.get("status") == "RECOGNIZED" and s_data.get("validity_status") == "ACTIVE"
            discrepancies = []
            if not is_recognized:
                discrepancies.append("DPIIT recognition is inactive or expired.")

            normalized = {
                "dipp_recognition_number": s_data.get("dipp_recognition_number"),
                "startup_name": s_data.get("startup_name"),
                "industry": s_data.get("industry"),
                "date_of_recognition": s_data.get("date_of_recognition"),
                "prior_turnover_waiver_eligible": s_data.get("gem_exemptions_eligible", {}).get("prior_turnover_waiver", False),
                "prior_experience_waiver_eligible": s_data.get("gem_exemptions_eligible", {}).get("prior_experience_waiver", False),
                "is_recognized": is_recognized
            }

            return NormalizedPortalResponse(
                portal_id=self.portal_id,
                portal_name=self.portal_name,
                category=self.category,
                status=PortalStatus.VERIFIED if is_recognized else PortalStatus.FLAGGED,
                is_valid=is_recognized,
                confidence_score=0.98,
                discrepancies=discrepancies,
                normalized_data=normalized,
                raw_data=raw,
                latency_ms=latency
            )
        except Exception as exc:
            return self.client.build_offline_fallback(str(exc), round((time.time() - start_t) * 1000, 2))
