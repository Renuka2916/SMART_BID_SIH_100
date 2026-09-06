import time
from typing import Optional

from app.integrations.base import BasePortalFetcher
from app.utils.response_normalizer import (
    BidderIdentifiers,
    NormalizedPortalResponse,
    PortalStatus
)
from app.mock_data.simulated_responses import get_simulated_epfo_response

class EpfoFetcher(BasePortalFetcher):
    portal_id = "EPFO"
    portal_name = "EPFO - Shram Suvidha Unified Portal"
    category = "Labor & Social Compliance"
    api_endpoint = "https://unifiedportal-epfo.epfindia.gov.in/api/v1/establishment"

    async def fetch_data(self, identifiers: BidderIdentifiers) -> NormalizedPortalResponse:
        start_t = time.time()
        try:
            raw = get_simulated_epfo_response(identifiers.epfo_code, identifiers.company_name)
            latency = round((time.time() - start_t) * 1000, 2)
            e_data = raw.get("data", {})

            discrepancies = []
            if e_data.get("defaulter_list", False):
                discrepancies.append("Establishment is currently listed on the EPFO Defaulter Roster.")

            if not e_data.get("payment_verified", False):
                discrepancies.append("Latest monthly ECR challan payment could not be verified.")

            is_valid = len(discrepancies) == 0 and raw.get("status") == "COMPLIANT"

            normalized = {
                "establishment_code": e_data.get("establishment_code"),
                "establishment_name": e_data.get("establishment_name"),
                "regional_office": e_data.get("regional_office"),
                "active_members_count": e_data.get("active_members_count"),
                "ecr_filing_status": e_data.get("ecr_filing_status"),
                "last_wage_month_filed": e_data.get("last_wage_month_filed"),
                "is_epfo_compliant": is_valid
            }

            return NormalizedPortalResponse(
                portal_id=self.portal_id,
                portal_name=self.portal_name,
                category=self.category,
                status=PortalStatus.VERIFIED if is_valid else PortalStatus.FLAGGED,
                is_valid=is_valid,
                confidence_score=0.97 if is_valid else 0.60,
                discrepancies=discrepancies,
                normalized_data=normalized,
                raw_data=raw,
                latency_ms=latency
            )
        except Exception as exc:
            return self.client.build_offline_fallback(str(exc), round((time.time() - start_t) * 1000, 2))
