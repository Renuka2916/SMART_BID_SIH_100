import time
from typing import Optional

from app.integrations.base import BasePortalFetcher
from app.utils.response_normalizer import (
    BidderIdentifiers,
    NormalizedPortalResponse,
    PortalStatus
)
from app.mock_data.simulated_responses import get_simulated_nsic_response

class NsicFetcher(BasePortalFetcher):
    portal_id = "NSIC"
    portal_name = "NSIC - Single Point Registration Scheme (SPRS)"
    category = "MSME & Industrial"
    api_endpoint = "https://www.nsic.co.in/api/v1/sprs-verify"

    async def fetch_data(self, identifiers: BidderIdentifiers) -> NormalizedPortalResponse:
        start_t = time.time()
        try:
            raw = get_simulated_nsic_response(identifiers.nsic_no, identifiers.company_name)
            latency = round((time.time() - start_t) * 1000, 2)
            n_data = raw.get("data", {})

            is_valid = raw.get("status") == "ACTIVE_CERTIFIED" and n_data.get("emd_exemption_qualified", False)
            discrepancies = []
            if not is_valid:
                discrepancies.append("NSIC SPRS certificate is inactive or ineligible for EMD waiver.")

            normalized = {
                "sprs_certificate_number": n_data.get("sprs_certificate_number"),
                "monetary_limit_inr": n_data.get("monetary_limit_inr"),
                "valid_from": n_data.get("valid_from"),
                "valid_up_to": n_data.get("valid_up_to"),
                "emd_exemption_qualified": n_data.get("emd_exemption_qualified", False),
                "is_active_certified": is_valid
            }

            return NormalizedPortalResponse(
                portal_id=self.portal_id,
                portal_name=self.portal_name,
                category=self.category,
                status=PortalStatus.VERIFIED if is_valid else PortalStatus.FLAGGED,
                is_valid=is_valid,
                confidence_score=0.97,
                discrepancies=discrepancies,
                normalized_data=normalized,
                raw_data=raw,
                latency_ms=latency
            )
        except Exception as exc:
            return self.client.build_offline_fallback(str(exc), round((time.time() - start_t) * 1000, 2))
