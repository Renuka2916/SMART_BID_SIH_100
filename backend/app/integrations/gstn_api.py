import time
from typing import Optional

from app.integrations.base import BasePortalFetcher
from app.utils.response_normalizer import (
    BidderIdentifiers,
    NormalizedPortalResponse,
    PortalStatus
)
from app.mock_data.simulated_responses import get_simulated_gstn_response

class GstnFetcher(BasePortalFetcher):
    portal_id = "GSTN"
    portal_name = "GSTN - Goods and Services Tax Network"
    category = "Statutory & Taxation"
    api_endpoint = "https://api.gst.gov.in/v1.0/taxpayer"

    async def fetch_data(self, identifiers: BidderIdentifiers) -> NormalizedPortalResponse:
        start_t = time.time()
        try:
            if not identifiers.gstin:
                return NormalizedPortalResponse(
                    portal_id=self.portal_id,
                    portal_name=self.portal_name,
                    category=self.category,
                    status=PortalStatus.FLAGGED,
                    is_valid=False,
                    confidence_score=0.0,
                    discrepancies=["No GSTIN provided for statutory tax verification."],
                    normalized_data={"status": "MISSING_GSTIN"},
                    latency_ms=round((time.time() - start_t) * 1000, 2)
                )

            raw = get_simulated_gstn_response(identifiers.gstin, identifiers.company_name)
            latency = round((time.time() - start_t) * 1000, 2)
            g_data = raw.get("data", {})

            discrepancies = []
            returned_name = g_data.get("legal_name", "") or g_data.get("trade_name", "")
            match_ok, note = self.check_name_alignment(identifiers.company_name, returned_name)
            if not match_ok and note:
                discrepancies.append(note)

            status_val = g_data.get("status", "")
            if status_val.upper() != "ACTIVE":
                discrepancies.append(f"GSTIN status is '{status_val}', not Active.")

            filing = g_data.get("filing_status", {})
            if "COMPLIANT" not in filing.get("gstr_3b_recency", ""):
                discrepancies.append("GSTR-3B return filing is overdue or non-compliant.")

            if g_data.get("e_way_bill_blocked", False):
                discrepancies.append("E-Way Bill generation is currently blocked due to tax default.")

            is_valid = len(discrepancies) == 0 and status_val.upper() == "ACTIVE"

            normalized = {
                "entity_name": returned_name,
                "gstin": g_data.get("gstin"),
                "active_status": status_val,
                "taxpayer_type": g_data.get("taxpayer_type"),
                "registration_date": g_data.get("registration_date"),
                "gstr_1_status": filing.get("gstr_1_recency"),
                "gstr_3b_status": filing.get("gstr_3b_recency"),
                "filings_count": len(filing.get("filings_history", [])),
                "compliance_rating": g_data.get("compliance_rating", "N/A")
            }

            return NormalizedPortalResponse(
                portal_id=self.portal_id,
                portal_name=self.portal_name,
                category=self.category,
                status=PortalStatus.VERIFIED if is_valid else PortalStatus.FLAGGED,
                is_valid=is_valid,
                confidence_score=0.99 if is_valid else 0.70,
                discrepancies=discrepancies,
                normalized_data=normalized,
                raw_data=raw,
                latency_ms=latency
            )
        except Exception as exc:
            return self.client.build_offline_fallback(str(exc), round((time.time() - start_t) * 1000, 2))
