import time
from typing import Optional

from app.integrations.base import BasePortalFetcher
from app.utils.response_normalizer import (
    BidderIdentifiers,
    NormalizedPortalResponse,
    PortalStatus
)
from app.mock_data.simulated_responses import get_simulated_blacklisting_response

class BlacklistingFetcher(BasePortalFetcher):
    portal_id = "NON_BLACKLIST"
    portal_name = "CPPP Debarment, GeM Watchlist & Vigilance Registry"
    category = "Integrity & Debarment"
    api_endpoint = "https://eprocure.gov.in/cppp/debarment-api"

    async def fetch_data(self, identifiers: BidderIdentifiers) -> NormalizedPortalResponse:
        start_t = time.time()
        try:
            raw = get_simulated_blacklisting_response(identifiers.company_name, identifiers.pan)
            latency = round((time.time() - start_t) * 1000, 2)
            b_data = raw.get("data", {})

            is_blacklisted = b_data.get("is_blacklisted", False)
            is_debarred = b_data.get("is_debarred", False)
            matches = b_data.get("database_matches", [])

            discrepancies = []
            if is_blacklisted or is_debarred:
                discrepancies.append(f"Entity appears on debarment registry with {len(matches)} match record(s).")
                for m in matches:
                    discrepancies.append(f"[{m.get('registry')}] {m.get('reason')} (Status: {m.get('current_status')})")

            is_clear = not is_blacklisted and not is_debarred

            normalized = {
                "is_blacklisted": is_blacklisted,
                "is_debarred": is_debarred,
                "vigilance_status": b_data.get("vigilance_clearance_status"),
                "debarment_records_count": len(matches),
                "cleared_for_procurement": is_clear
            }

            return NormalizedPortalResponse(
                portal_id=self.portal_id,
                portal_name=self.portal_name,
                category=self.category,
                status=PortalStatus.VERIFIED if is_clear else PortalStatus.FLAGGED,
                is_valid=is_clear,
                confidence_score=0.99 if is_clear else 0.40,
                discrepancies=discrepancies,
                normalized_data=normalized,
                raw_data=raw,
                latency_ms=latency
            )
        except Exception as exc:
            return self.client.build_offline_fallback(str(exc), round((time.time() - start_t) * 1000, 2))
