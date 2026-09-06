import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple

from app.integrations.base import BasePortalFetcher
from app.utils.response_normalizer import (
    BidderIdentifiers,
    NormalizedPortalResponse,
    PortalStatus
)

# Import all 15 fetchers
from app.integrations.udyam_api import UdyamFetcher
from app.integrations.gstn_api import GstnFetcher
from app.integrations.pan_income_tax_api import PanIncomeTaxFetcher
from app.integrations.mca21_api import Mca21Fetcher
from app.integrations.epfo_api import EpfoFetcher
from app.integrations.esic_api import EsicFetcher
from app.integrations.startup_india_api import StartupIndiaFetcher
from app.integrations.nsic_api import NsicFetcher
from app.integrations.digilocker_api import DigiLockerFetcher
from app.integrations.blacklisting_api import BlacklistingFetcher
from app.integrations.dpiit_mii_api import DpiitMiiFetcher
from app.integrations.bis_api import BisFetcher
from app.integrations.oem_auth_api import OemAuthFetcher
from app.integrations.gem_incident_api import GemIncidentFetcher
from app.integrations.turnover_ca_api import TurnoverCaFetcher

logger = logging.getLogger("portal_integration_manager")

class PortalIntegrationManager:
    """
    Orchestration Engine for Multi-Portal Integrations:
    - Central registry for 15+ statutory government API fetchers.
    - Concurrent asynchronous parallel execution with asyncio.
    - Fault-tolerant error containment and fallback reporting.
    - Standardized score aggregation and discrepancy extraction.
    """
    def __init__(self):
        self._fetchers: Dict[str, BasePortalFetcher] = {}
        self._register_all_fetchers()

    def _register_all_fetchers(self):
        fetcher_instances = [
            UdyamFetcher(),
            GstnFetcher(),
            PanIncomeTaxFetcher(),
            Mca21Fetcher(),
            EpfoFetcher(),
            EsicFetcher(),
            StartupIndiaFetcher(),
            NsicFetcher(),
            DigiLockerFetcher(),
            BlacklistingFetcher(),
            DpiitMiiFetcher(),
            BisFetcher(),
            OemAuthFetcher(),
            GemIncidentFetcher(),
            TurnoverCaFetcher()
        ]
        for f in fetcher_instances:
            self._fetchers[f.portal_id] = f

    def get_all_registered_portals(self) -> List[Dict[str, Any]]:
        """Returns metadata for all registered government portal adapters."""
        return [
            {
                "portal_id": f.portal_id,
                "portal_name": f.portal_name,
                "category": f.category,
                "endpoint": f.api_endpoint,
                "status": "Connected",
                "mode": "Simulation / Mock Enabled" if f.use_mock else "Live REST Gateway",
                "timeout_seconds": f.timeout_seconds,
                "max_retries": f.max_retries
            }
            for f in self._fetchers.values()
        ]

    def get_fetcher(self, portal_id: str) -> Optional[BasePortalFetcher]:
        return self._fetchers.get(portal_id)

    async def fetch_single_portal(
        self,
        portal_id: str,
        identifiers: BidderIdentifiers
    ) -> NormalizedPortalResponse:
        """Fetches and normalizes data from a single specific portal."""
        fetcher = self._fetchers.get(portal_id)
        if not fetcher:
            return NormalizedPortalResponse(
                portal_id=portal_id,
                portal_name="Unknown Portal",
                category="Unknown",
                status=PortalStatus.FAILED,
                is_valid=False,
                confidence_score=0.0,
                discrepancies=[f"No registered fetcher adapter for portal '{portal_id}'."]
            )
        try:
            return await fetcher.fetch_data(identifiers)
        except Exception as exc:
            logger.error(f"Error fetching from {portal_id}: {exc}")
            return fetcher.client.build_offline_fallback(str(exc))

    async def fetch_all_for_bidder(
        self,
        identifiers: BidderIdentifiers,
        portal_keys: Optional[List[str]] = None
    ) -> Dict[str, NormalizedPortalResponse]:
        """
        Executes parallel asynchronous calls across all (or requested) statutory portals.
        Uses asyncio.gather with return_exceptions=True for total isolation.
        """
        target_keys = portal_keys if portal_keys else list(self._fetchers.keys())
        keys_to_fetch = [k for k in target_keys if k in self._fetchers]

        tasks = [self._fetchers[k].fetch_data(identifiers) for k in keys_to_fetch]
        raw_results = await asyncio.gather(*tasks, return_exceptions=True)

        results: Dict[str, NormalizedPortalResponse] = {}
        for key, res in zip(keys_to_fetch, raw_results):
            fetcher = self._fetchers[key]
            if isinstance(res, Exception):
                logger.error(f"Async exception in {key}: {res}")
                results[key] = fetcher.client.build_offline_fallback(str(res))
            elif isinstance(res, NormalizedPortalResponse):
                results[key] = res
            else:
                results[key] = fetcher.client.build_offline_fallback("Unknown return type")

        return results

    def aggregate_compliance(
        self,
        results: Dict[str, NormalizedPortalResponse]
    ) -> Tuple[float, str, List[str]]:
        """
        Computes statutory compliance score (0-100), composite status, and consolidated discrepancies.
        """
        if not results:
            return 0.0, "UNDER_REVIEW", ["No portal verifications performed."]

        valid_count = sum(1 for r in results.values() if r.is_valid and r.status == PortalStatus.VERIFIED)
        total = len(results)
        score = round((valid_count / total) * 100.0, 1)

        all_discrepancies = []
        for pid, r in results.items():
            for d in r.discrepancies:
                all_discrepancies.append(f"[{r.portal_name}] {d}")

        if any(r.status == PortalStatus.FLAGGED for r in results.values()):
            status = "FLAGGED"
        elif score >= 80.0:
            status = "COMPLIANT"
        elif score >= 50.0:
            status = "UNDER_REVIEW"
        else:
            status = "NON_COMPLIANT"

        return score, status, all_discrepancies

# Singleton instance
portal_manager = PortalIntegrationManager()
