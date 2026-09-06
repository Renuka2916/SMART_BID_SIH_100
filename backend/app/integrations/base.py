import os
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

from app.utils.api_client import GovtAPIClient
from app.utils.response_normalizer import (
    BidderIdentifiers,
    NormalizedPortalResponse,
    PortalStatus,
    calculate_name_similarity,
    normalize_legal_name
)

class BasePortalFetcher(ABC):
    """
    Abstract Base Class for all 15 Government Statutory Verification Portal Fetchers.
    Ensures a standardized interface across heterogeneous external APIs.
    """
    portal_id: str
    portal_name: str
    category: str
    api_endpoint: str = "https://api.gov.in/sample"
    timeout_seconds: float = 4.0
    max_retries: int = 3
    rate_limit_per_second: int = 10

    def __init__(self):
        self.use_mock = os.getenv("MOCK_GOVT_APIS", "true").lower() in ("true", "1", "yes")
        self.client = GovtAPIClient(
            portal_id=self.portal_id,
            portal_name=self.portal_name,
            category=self.category,
            timeout_seconds=self.timeout_seconds,
            max_retries=self.max_retries,
            rate_limit_per_second=self.rate_limit_per_second
        )

    @abstractmethod
    async def fetch_data(self, identifiers: BidderIdentifiers) -> NormalizedPortalResponse:
        """
        Executes external API call or mock fallback, normalizes payload, and verifies compliance.
        Must return a NormalizedPortalResponse.
        """
        pass

    def check_name_alignment(
        self,
        bidder_company_name: str,
        portal_returned_name: str,
        threshold: float = 0.75
    ) -> tuple[bool, Optional[str]]:
        """Verifies if bidder name in tender matches legal registered name on portal."""
        sim = calculate_name_similarity(bidder_company_name, portal_returned_name)
        if sim >= threshold:
            return True, None
        return False, (
            f"Name discrepancy detected: Bidder registered as '{bidder_company_name}' "
            f"but {self.portal_name} lists legal entity as '{portal_returned_name}' (Match: {int(sim*100)}%)."
        )
