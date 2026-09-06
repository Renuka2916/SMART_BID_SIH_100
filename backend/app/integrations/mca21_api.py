import time
from typing import Optional

from app.integrations.base import BasePortalFetcher
from app.utils.response_normalizer import (
    BidderIdentifiers,
    NormalizedPortalResponse,
    PortalStatus
)
from app.mock_data.simulated_responses import get_simulated_mca21_response

class Mca21Fetcher(BasePortalFetcher):
    portal_id = "MCA21"
    portal_name = "Ministry of Corporate Affairs (MCA21)"
    category = "Corporate & Legal Identity"
    api_endpoint = "https://mca.gov.in/api/v1/company-master"

    async def fetch_data(self, identifiers: BidderIdentifiers) -> NormalizedPortalResponse:
        start_t = time.time()
        try:
            raw = get_simulated_mca21_response(identifiers.cin, identifiers.company_name)
            latency = round((time.time() - start_t) * 1000, 2)
            m_data = raw.get("data", {})

            discrepancies = []
            returned_name = m_data.get("company_name", "")
            match_ok, note = self.check_name_alignment(identifiers.company_name, returned_name)
            if not match_ok and note:
                discrepancies.append(note)

            status_val = raw.get("status", "")
            if status_val != "ACTIVE":
                discrepancies.append(f"Company status on MCA21 is '{status_val}', expected ACTIVE.")

            directors = m_data.get("directors", [])
            for d in directors:
                if d.get("disqualified", False):
                    discrepancies.append(f"Director {d.get('name')} (DIN: {d.get('din')}) is flagged as disqualified.")

            is_valid = len(discrepancies) == 0 and status_val == "ACTIVE"

            normalized = {
                "entity_name": returned_name,
                "cin": m_data.get("cin"),
                "roc_code": m_data.get("roc_code"),
                "class_of_company": m_data.get("class_of_company"),
                "paid_up_capital_inr": m_data.get("paid_up_capital_inr"),
                "active_compliance": m_data.get("active_compliance"),
                "directors_count": len(directors),
                "is_active_compliant": is_valid
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
