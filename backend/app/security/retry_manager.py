import asyncio
import inspect
import random
import logging
from typing import Callable, Any, Optional
from app.security.failure_handling import get_circuit_breaker, PortalOutageException

logger = logging.getLogger("security_retry_manager")

class RetryPolicy:
    """Configurable retry policy with exponential backoff and randomized jitter."""
    def __init__(
        self,
        max_retries: int = 3,
        base_delay_sec: float = 0.1,
        max_delay_sec: float = 2.0,
        backoff_factor: float = 2.0,
        jitter: bool = True
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay_sec
        self.max_delay = max_delay_sec
        self.backoff_factor = backoff_factor
        self.jitter = jitter

    def compute_delay(self, attempt: int) -> float:
        delay = min(self.max_delay, self.base_delay * (self.backoff_factor ** attempt))
        if self.jitter:
            delay += random.uniform(0, self.base_delay)
        return delay

DEFAULT_RETRY_POLICY = RetryPolicy()

async def fetch_with_retry(
    portal_id: str,
    fetch_func: Callable[..., Any],
    *args,
    policy: Optional[RetryPolicy] = None,
    **kwargs
) -> Any:
    """
    Executes an external portal fetch with circuit breaker awareness and exponential retry logic.
    """
    pol = policy or DEFAULT_RETRY_POLICY
    cb = get_circuit_breaker(portal_id)

    if not cb.can_execute():
        logger.warning(f"Circuit breaker for portal '{portal_id}' is OPEN. Failing fast to offline fallback.")
        raise PortalOutageException(
            portal_id=portal_id,
            message=f"Statutory portal '{portal_id}' is temporarily offline (Circuit Breaker OPEN).",
            status_code=503
        )

    last_exc = None
    for attempt in range(pol.max_retries):
        try:
            if inspect.iscoroutinefunction(fetch_func):
                result = await fetch_func(*args, **kwargs)
            else:
                result = fetch_func(*args, **kwargs)

            cb.record_success()
            return result
        except Exception as exc:
            last_exc = exc
            cb.record_failure()
            delay = pol.compute_delay(attempt)
            logger.warning(
                f"[Portal Retry] Attempt {attempt + 1}/{pol.max_retries} for portal '{portal_id}' failed: {exc}. Retrying in {delay:.2f}s..."
            )
            if attempt < pol.max_retries - 1:
                await asyncio.sleep(delay)

    logger.error(f"[Portal Failure] All {pol.max_retries} retry attempts exhausted for portal '{portal_id}': {last_exc}")
    raise PortalOutageException(
        portal_id=portal_id,
        message=f"Government portal '{portal_id}' unreachable after {pol.max_retries} attempts: {last_exc}"
    )
