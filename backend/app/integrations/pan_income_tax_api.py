import time
from typing import Optional

from app.integrations.base import BasePortalFetcher
from app.utils.response_normalizer import (
    BidderIdentifiers,
    NormalizedPortalResponse,
    PortalStatus
)
from app.mock_data.simulated_responses import get_simulated_pan_cbdt_response

class PanIncomeTaxFetcher(BasePortalFetcher):
    portal_id = "PAN_INCOME_TAX"
    portal_name = "CBDT - Income Tax Department / PAN Portal"
    category = "Statutory & Taxation"
    api_endpoint = "https://eportal.incometax.gov.in/api/v1/pan-verify"

    async def fetch_data(self, identifiers: BidderIdentifiers) -> NormalizedPortalResponse:
        start_t = time.time()
        try:
            if not identifiers.pan:
                return NormalizedPortalResponse(
                    portal_id=self.portal_id,
                    portal_name=self.portal_name,
                    category=self.category,
                    status=PortalStatus.FLAGGED,
                    is_valid=False,
                    confidence_score=0.0,
                    discrepancies=["No PAN provided for statutory income tax verification."],
                    normalized_data={"status": "MISSING_PAN"},
                    latency_ms=round((time.time() - start_t) * 1000, 2)
                )

            raw = get_simulated_pan_cbdt_response(identifiers.pan, identifiers.company_name)
            latency = round((time.time() - start_t) * 1000, 2)
            p_data = raw.get("data", {})

            discrepancies = []
            returned_name = p_data.get("registered_name", "")
            match_ok, note = self.check_name_alignment(identifiers.company_name, returned_name)
            if not match_ok and note:
                discrepancies.append(note)

            pan_status = p_data.get("pan_status", "")
            if pan_status != "EXISTING_AND_VALID":
                discrepancies.append(f"PAN status is invalid or inactive: {pan_status}.")

            itr_info = p_data.get("itr_compliance_status", {})
            if itr_info.get("is_specified_person_u_s_206ab_206cca", False):
                discrepancies.append("Entity is flagged as a specified non-filer under Section 206AB/206CCA.")

            filings = itr_info.get("itr_filing_history", [])
            if len(filings) < 2:
                discrepancies.append(f"Insufficient ITR filing history: found {len(filings)} years, tender requires at least 2.")

            is_valid = len(discrepancies) == 0 and pan_status == "EXISTING_AND_VALID"

            normalized = {
                "entity_name": returned_name,
                "pan": p_data.get("pan"),
                "pan_status": pan_status,
                "entity_category": p_data.get("category"),
                "section_206ab_clear": not itr_info.get("is_specified_person_u_s_206ab_206cca", False),
                "itr_filings_count": len(filings),
                "latest_itr_ay": filings[0].get("ay") if filings else None
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
