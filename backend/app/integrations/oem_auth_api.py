import time
from typing import Optional

from app.integrations.base import BasePortalFetcher
from app.utils.response_normalizer import (
    BidderIdentifiers,
    NormalizedPortalResponse,
    PortalStatus
)
from app.mock_data.simulated_responses import get_simulated_oem_auth_response

class OemAuthFetcher(BasePortalFetcher):
    portal_id = "OEM_AUTH"
    portal_name = "OEM Manufacturer Authorization Registry"
    category = "Technical Eligibility"
    api_endpoint = "https://oem-verify.gem.gov.in/api/v1/maf"

    async def fetch_data(self, identifiers: BidderIdentifiers) -> NormalizedPortalResponse:
        start_t = time.time()
        try:
            raw = get_simulated_oem_auth_response(identifiers.company_name)
            latency = round((time.time() - start_t) * 1000, 2)
            o_data = raw.get("data", {})

            is_authentic = raw.get("status") == "AUTHENTIC"
            discrepancies = []
            if not is_authentic:
                discrepancies.append("OEM Authorization Form could not be authenticated against OEM principal ledger.")

            normalized = {
                "oem_principal": o_data.get("oem_principal"),
                "maf_code": o_data.get("maf_code"),
                "authorization_tier": o_data.get("authorization_tier"),
                "scope_of_authorization": o_data.get("scope_of_authorization"),
                "oem_signatory_email": o_data.get("oem_signatory_email"),
                "is_oem_authorized": is_authentic
            }

            return NormalizedPortalResponse(
                portal_id=self.portal_id,
                portal_name=self.portal_name,
                category=self.category,
                status=PortalStatus.VERIFIED if is_authentic else PortalStatus.FLAGGED,
                is_valid=is_authentic,
                confidence_score=0.98,
                discrepancies=discrepancies,
                normalized_data=normalized,
                raw_data=raw,
                latency_ms=latency
            )
        except Exception as exc:
            return self.client.build_offline_fallback(str(exc), round((time.time() - start_t) * 1000, 2))
