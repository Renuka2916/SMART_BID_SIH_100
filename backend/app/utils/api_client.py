import time
import asyncio
import logging
from typing import Dict, Any, Optional
import httpx

from app.utils.response_normalizer import NormalizedPortalResponse, PortalStatus

logger = logging.getLogger("govt_api_client")

class GovtAPIClient:
    """
    Resilient Asynchronous HTTP Client for Government Portals:
    - Exponential backoff retry on network failures or 5xx responses.
    - Configurable timeouts per portal.
    - Simple rate limiting token tracker.
    - Safe fallback when service is offline or unreachable.
    """
    def __init__(
        self,
        portal_id: str,
        portal_name: str,
        category: str,
        timeout_seconds: float = 5.0,
        max_retries: int = 3,
        rate_limit_per_second: int = 10
    ):
        self.portal_id = portal_id
        self.portal_name = portal_name
        self.category = category
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.rate_limit_per_second = rate_limit_per_second
        self._last_call_time = 0.0

    async def _throttle(self):
        """Simple delay throttle for rate limiting."""
        min_interval = 1.0 / max(self.rate_limit_per_second, 1)
        now = time.time()
        elapsed = now - self._last_call_time
        if elapsed < min_interval:
            await asyncio.sleep(min_interval - elapsed)
        self._last_call_time = time.time()

    async def execute_request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Executes HTTP request with exponential backoff retry.
        Raises httpx.HTTPError or asyncio.TimeoutError on persistent failure.
        """
        await self._throttle()
        delay = 0.5

        for attempt in range(1, self.max_retries + 1):
            try:
                start_t = time.time()
                async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                    resp = await client.request(
                        method=method,
                        url=url,
                        headers=headers,
                        json=json_data,
                        params=params
                    )
                    latency = round((time.time() - start_t) * 1000, 2)

                    # Successful response
                    if resp.status_code < 400:
                        try:
                            data = resp.json()
                        except Exception:
                            data = {"raw_text": resp.text}
                        return {
                            "status_code": resp.status_code,
                            "data": data,
                            "latency_ms": latency,
                            "attempt": attempt
                        }
                    
                    # 4xx Client Errors - do not retry unless 429
                    if 400 <= resp.status_code < 500 and resp.status_code != 429:
                        return {
                            "status_code": resp.status_code,
                            "data": resp.text,
                            "latency_ms": latency,
                            "attempt": attempt,
                            "error": f"Client error: HTTP {resp.status_code}"
                        }

                    # Server error or rate limit 429 - eligible for retry
                    logger.warning(
                        f"[{self.portal_id}] Attempt {attempt}/{self.max_retries} returned HTTP {resp.status_code}. Retrying in {delay}s..."
                    )

            except (httpx.RequestError, asyncio.TimeoutError) as exc:
                logger.warning(
                    f"[{self.portal_id}] Attempt {attempt}/{self.max_retries} connection failed: {str(exc)}. Retrying in {delay}s..."
                )
                if attempt == self.max_retries:
                    raise exc

            await asyncio.sleep(delay)
            delay *= 2  # Exponential backoff

        raise httpx.RequestError(f"[{self.portal_id}] Failed after {self.max_retries} attempts.")

    def build_offline_fallback(self, error_reason: str, latency_ms: float = 0.0) -> NormalizedPortalResponse:
        """Constructs an OFFLINE status fallback response when remote API fails."""
        return NormalizedPortalResponse(
            portal_id=self.portal_id,
            portal_name=self.portal_name,
            category=self.category,
            status=PortalStatus.OFFLINE,
            is_valid=False,
            confidence_score=0.0,
            discrepancies=[f"Government portal {self.portal_name} is temporarily offline or unreachable: {error_reason}"],
            normalized_data={"connectivity_status": "OFFLINE", "fallback_applied": True},
            raw_data={"error": error_reason},
            latency_ms=latency_ms,
            error_message=error_reason
        )
