import time
from typing import Optional

from app.integrations.base import BasePortalFetcher
from app.utils.response_normalizer import (
    BidderIdentifiers,
    NormalizedPortalResponse,
    PortalStatus
)
from app.mock_data.simulated_responses import get_simulated_udyam_response

class UdyamFetcher(BasePortalFetcher):
    portal_id = "UDYAM"
    portal_name = "Ministry of MSME - Udyam Registration Portal"
    category = "MSME & Industrial"
    api_endpoint = "https://udyamregistration.gov.in/api/v1/verify"

    async def fetch_data(self, identifiers: BidderIdentifiers) -> NormalizedPortalResponse:
        start_t = time.time()
        try:
            if not identifiers.udyam_no and not identifiers.company_name:
                return NormalizedPortalResponse(
                    portal_id=self.portal_id,
                    portal_name=self.portal_name,
                    category=self.category,
                    status=PortalStatus.FLAGGED,
                    is_valid=False,
                    confidence_score=0.0,
                    discrepancies=["No Udyam registration number provided by bidder."],
                    normalized_data={"status": "MISSING_IDENTIFIER"},
                    latency_ms=round((time.time() - start_t) * 1000, 2)
                )

            # In production: make real request via self.client.execute_request(...)
            # In mock/demo mode: generate authentic simulated response
            raw = get_simulated_udyam_response(identifiers.udyam_no, identifiers.company_name)
            latency = round((time.time() - start_t) * 1000, 2)
            u_data = raw.get("data", {})

            # Discrepancy checks
            discrepancies = []
            returned_name = u_data.get("enterprise_name", "")
            match_ok, note = self.check_name_alignment(identifiers.company_name, returned_name)
            if not match_ok and note:
                discrepancies.append(note)

            status_val = u_data.get("status", "")
            if status_val != "ACTIVE":
                discrepancies.append(f"Udyam registration status is '{status_val}', not ACTIVE.")

            is_valid = len(discrepancies) == 0 and status_val == "ACTIVE"

            normalized = {
                "entity_name": returned_name,
                "registration_number": u_data.get("udyam_registration_number"),
                "classification": u_data.get("classification"),
                "major_activity": u_data.get("major_activity"),
                "active_status": status_val,
                "date_of_registration": u_data.get("date_of_registration"),
                "msme_benefits_qualified": is_valid
            }

            return NormalizedPortalResponse(
                portal_id=self.portal_id,
                portal_name=self.portal_name,
                category=self.category,
                status=PortalStatus.VERIFIED if is_valid else PortalStatus.FLAGGED,
                is_valid=is_valid,
                confidence_score=0.98 if is_valid else 0.65,
                discrepancies=discrepancies,
                normalized_data=normalized,
                raw_data=raw,
                latency_ms=latency
            )
        except Exception as exc:
            return self.client.build_offline_fallback(str(exc), round((time.time() - start_t) * 1000, 2))
