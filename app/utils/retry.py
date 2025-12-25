import asyncio
import httpx
import logging
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

logger = logging.getLogger(__name__)

def network_retry(
    attempts: int = 3,
    min_wait: int = 1,
    max_wait: int = 8,
):
    return retry(
        stop=stop_after_attempt(attempts),
        wait=wait_exponential(multiplier=2, min=min_wait, max=max_wait),
        retry=retry_if_exception_type((
            httpx.ConnectError,
            httpx.ReadTimeout,
            httpx.RemoteProtocolError,
            asyncio.TimeoutError,
            ConnectionError,
        )),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )