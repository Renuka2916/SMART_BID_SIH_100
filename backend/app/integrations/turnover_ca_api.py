import time
from typing import Optional

from app.integrations.base import BasePortalFetcher
from app.utils.response_normalizer import (
    BidderIdentifiers,
    NormalizedPortalResponse,
    PortalStatus
)
from app.mock_data.simulated_responses import get_simulated_turnover_ca_response

class TurnoverCaFetcher(BasePortalFetcher):
    portal_id = "TURNOVER"
    portal_name = "ICAI UDIN Registry & Corporate Financials"
    category = "Financial Eligibility"
    api_endpoint = "https://udin.icai.org/api/v1/verify-udin"

    async def fetch_data(self, identifiers: BidderIdentifiers) -> NormalizedPortalResponse:
        start_t = time.time()
        try:
            raw = get_simulated_turnover_ca_response(identifiers.company_name)
            latency = round((time.time() - start_t) * 1000, 2)
            t_data = raw.get("data", {})

            solvency = t_data.get("solvency_status", "UNKNOWN")
            is_valid = raw.get("status") == "AUDITED_VALID" and solvency == "SOLVENT"

            discrepancies = []
            if solvency != "SOLVENT":
                discrepancies.append(f"Entity solvency status is '{solvency}', expected SOLVENT.")

            turnover_info = t_data.get("financial_turnover", {})
            avg_to = turnover_info.get("avg_3yr_turnover_inr_crores", 0.0)

            normalized = {
                "udin_number": t_data.get("udin_number"),
                "ca_firm": t_data.get("chartered_accountant_firm"),
                "avg_3yr_turnover_crores": f"₹ {avg_to} Cr",
                "net_worth_crores": f"₹ {t_data.get('net_worth_inr_crores')} Cr",
                "solvency_status": solvency,
                "udin_verified": is_valid
            }

            return NormalizedPortalResponse(
                portal_id=self.portal_id,
                portal_name=self.portal_name,
                category=self.category,
                status=PortalStatus.VERIFIED if is_valid else PortalStatus.FLAGGED,
                is_valid=is_valid,
                confidence_score=0.99,
                discrepancies=discrepancies,
                normalized_data=normalized,
                raw_data=raw,
                latency_ms=latency
            )
        except Exception as exc:
            return self.client.build_offline_fallback(str(exc), round((time.time() - start_t) * 1000, 2))
