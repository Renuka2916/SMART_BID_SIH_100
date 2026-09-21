import time
from typing import Optional

from app.integrations.base import BasePortalFetcher
from app.utils.response_normalizer import (
    BidderIdentifiers,
    NormalizedPortalResponse,
    PortalStatus
)
from app.mock_data.simulated_responses import get_simulated_gem_incident_response

class GemIncidentFetcher(BasePortalFetcher):
    portal_id = "GEM_INCIDENT"
    portal_name = "SmartBid Incident Management & Seller Rating System"
    category = "Platform Integrity & History"
    api_endpoint = "https://incident.smartbid.gov.in/api/v1/seller-standing"

    async def fetch_data(self, identifiers: BidderIdentifiers) -> NormalizedPortalResponse:
        start_t = time.time()
        try:
            raw = get_simulated_gem_incident_response(identifiers.company_name)
            latency = round((time.time() - start_t) * 1000, 2)
            g_data = raw.get("data", {})

            rating = g_data.get("overall_seller_rating", 5.0)
            open_incidents = g_data.get("open_incidents_count", 0)

            discrepancies = []
            if open_incidents > 0:
                discrepancies.append(f"Seller has {open_incidents} unresolved incident(s) on SmartBid marketplace.")
            if rating < 4.0:
                discrepancies.append(f"Seller rating ({rating}/5.0) is below standard threshold (4.0).")

            is_clear = len(discrepancies) == 0

            normalized = {
                "overall_seller_rating": rating,
                "total_completed_orders": g_data.get("total_completed_orders"),
                "delivery_timeliness_pct": f"{g_data.get('delivery_timeliness_pct')}%",
                "open_incidents_count": open_incidents,
                "standing_status": raw.get("status"),
                "is_platform_reputable": is_clear
            }

            return NormalizedPortalResponse(
                portal_id=self.portal_id,
                portal_name=self.portal_name,
                category=self.category,
                status=PortalStatus.VERIFIED if is_clear else PortalStatus.FLAGGED,
                is_valid=is_clear,
                confidence_score=0.98,
                discrepancies=discrepancies,
                normalized_data=normalized,
                raw_data=raw,
                latency_ms=latency
            )
        except Exception as exc:
            return self.client.build_offline_fallback(str(exc), round((time.time() - start_t) * 1000, 2))
