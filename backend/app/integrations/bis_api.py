import time
from typing import Optional

from app.integrations.base import BasePortalFetcher
from app.utils.response_normalizer import (
    BidderIdentifiers,
    NormalizedPortalResponse,
    PortalStatus
)
from app.mock_data.simulated_responses import get_simulated_bis_response

class BisFetcher(BasePortalFetcher):
    portal_id = "BIS_CERTIFICATION"
    portal_name = "Bureau of Indian Standards (BIS)"
    category = "Technical Standards & Quality"
    api_endpoint = "https://www.services.bis.gov.in/api/v1/crs-search"

    async def fetch_data(self, identifiers: BidderIdentifiers) -> NormalizedPortalResponse:
        start_t = time.time()
        try:
            raw = get_simulated_bis_response(identifiers.company_name)
            latency = round((time.time() - start_t) * 1000, 2)
            b_data = raw.get("data", {})

            status_val = b_data.get("status", "")
            is_valid = status_val == "OPERATIVE"
            discrepancies = []
            if not is_valid:
                discrepancies.append(f"BIS certification status is '{status_val}', expected OPERATIVE.")

            normalized = {
                "registration_number": b_data.get("registration_number"),
                "bis_standard": b_data.get("bis_standard"),
                "product_category": b_data.get("product_category"),
                "status": status_val,
                "valid_till": b_data.get("valid_till"),
                "is_operative": is_valid
            }

            return NormalizedPortalResponse(
                portal_id=self.portal_id,
                portal_name=self.portal_name,
                category=self.category,
                status=PortalStatus.VERIFIED if is_valid else PortalStatus.FLAGGED,
                is_valid=is_valid,
                confidence_score=0.96,
                discrepancies=discrepancies,
                normalized_data=normalized,
                raw_data=raw,
                latency_ms=latency
            )
        except Exception as exc:
            return self.client.build_offline_fallback(str(exc), round((time.time() - start_t) * 1000, 2))
