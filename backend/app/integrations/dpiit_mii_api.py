import time
from typing import Optional

from app.integrations.base import BasePortalFetcher
from app.utils.response_normalizer import (
    BidderIdentifiers,
    NormalizedPortalResponse,
    PortalStatus
)
from app.mock_data.simulated_responses import get_simulated_dpiit_mii_response

class DpiitMiiFetcher(BasePortalFetcher):
    portal_id = "MAKE_IN_INDIA"
    portal_name = "DPIIT Make in India (Local Content) Portal"
    category = "Policy & Preferential Eligibility"
    api_endpoint = "https://dpiit.gov.in/api/v1/mii-compliance"

    async def fetch_data(self, identifiers: BidderIdentifiers) -> NormalizedPortalResponse:
        start_t = time.time()
        try:
            raw = get_simulated_dpiit_mii_response(identifiers.company_name)
            latency = round((time.time() - start_t) * 1000, 2)
            d_data = raw.get("data", {})

            local_pct = d_data.get("local_content_percentage", 0.0)
            discrepancies = []
            if local_pct < 20.0:
                discrepancies.append(f"Local content ({local_pct}%) does not meet minimum threshold (20% for Class-II).")

            if not d_data.get("ca_declaration_attached", False):
                discrepancies.append("Statutory CA / Cost Auditor local content certification is missing.")

            is_valid = local_pct >= 20.0 and d_data.get("preference_benefit_eligible", False)

            normalized = {
                "local_content_percentage": f"{local_pct}%",
                "supplier_classification": d_data.get("supplier_classification"),
                "ca_declaration_attached": d_data.get("ca_declaration_attached"),
                "statutory_declaration_ref": d_data.get("statutory_declaration_ref"),
                "preference_benefit_eligible": is_valid
            }

            return NormalizedPortalResponse(
                portal_id=self.portal_id,
                portal_name=self.portal_name,
                category=self.category,
                status=PortalStatus.VERIFIED if is_valid else PortalStatus.FLAGGED,
                is_valid=is_valid,
                confidence_score=0.95,
                discrepancies=discrepancies,
                normalized_data=normalized,
                raw_data=raw,
                latency_ms=latency
            )
        except Exception as exc:
            return self.client.build_offline_fallback(str(exc), round((time.time() - start_t) * 1000, 2))
