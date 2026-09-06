import time
from typing import Optional

from app.integrations.base import BasePortalFetcher
from app.utils.response_normalizer import (
    BidderIdentifiers,
    NormalizedPortalResponse,
    PortalStatus
)
from app.mock_data.simulated_responses import get_simulated_digilocker_response

class DigiLockerFetcher(BasePortalFetcher):
    portal_id = "DIGILOCKER"
    portal_name = "DigiLocker National Repository (MeitY)"
    category = "Document Integrity & Cryptography"
    api_endpoint = "https://digilocker.gov.in/api/v1/verify-docket"

    async def fetch_data(self, identifiers: BidderIdentifiers) -> NormalizedPortalResponse:
        start_t = time.time()
        try:
            raw = get_simulated_digilocker_response(identifiers.company_name)
            latency = round((time.time() - start_t) * 1000, 2)
            d_data = raw.get("data", {})

            sig = d_data.get("digital_signature", {})
            sig_valid = sig.get("cert_validity") == "VALID" and sig.get("ocsp_revocation_status") == "GOOD"
            discrepancies = []
            if not sig_valid:
                discrepancies.append("Digital signature failed PKCS#7 / OCSP validation check.")

            normalized = {
                "repository_uri": d_data.get("repository_uri"),
                "tamper_proof_checksum": d_data.get("tamper_proof_checksum"),
                "digital_signature_format": sig.get("format"),
                "signer_cn": sig.get("signer_cn"),
                "signature_valid": sig_valid,
                "verified_credentials": d_data.get("verified_credentials", []),
                "is_digilocker_verified": sig_valid
            }

            return NormalizedPortalResponse(
                portal_id=self.portal_id,
                portal_name=self.portal_name,
                category=self.category,
                status=PortalStatus.VERIFIED if sig_valid else PortalStatus.FLAGGED,
                is_valid=sig_valid,
                confidence_score=1.0 if sig_valid else 0.5,
                discrepancies=discrepancies,
                normalized_data=normalized,
                raw_data=raw,
                latency_ms=latency
            )
        except Exception as exc:
            return self.client.build_offline_fallback(str(exc), round((time.time() - start_t) * 1000, 2))
