import asyncio
import random
import uuid
import httpx
from typing import Any, Dict, Optional
from core.network.retry import async_retry
from core.logging.logger import logger


async def _jitter_backoff(attempt: int) -> None:
    """Non-linear exponential backoff with jitter (from partner project).
    Prevents thundering-herd retries under load.
    Delay = 2^attempt (capped at 30s) + random(0.5..1.5) * (attempt+1)
    """
    base = min(2 ** attempt, 30)
    jitter = random.uniform(0.5, 1.5) * (attempt + 1)
    await asyncio.sleep(base + jitter)


class BaseAPIClient:
    """
    Centralized API Client with tracing and retry capabilities.
    """
    def __init__(self, base_url: str, headers: Optional[Dict[str, str]] = None, proxy: Optional[str] = None):
        self.base_url = base_url
        self.headers = headers or {}

        # Configure client with proxy + connection limits (from partner project)
        limits = httpx.Limits(max_connections=100, max_keepalive_connections=50)
        mounts = {}
        if proxy:
            mounts = {"all://": httpx.AsyncHTTPTransport(proxy=proxy)}
            logger.info("Client initialized with proxy", proxy=proxy)

        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=self.headers,
            mounts=mounts,
            http2=True,
            timeout=httpx.Timeout(15.0, connect=5.0),
            limits=limits,
        )

    @async_retry(max_retries=3, base_delay=0.5)
    async def request(
        self,
        method: str,
        path: str,
        **kwargs
    ) -> httpx.Response:
        """
        Executes an HTTP request with automatic retries and logging.
        Injects X-Correlation-Id / X-Request-Id for per-request traceability.
        """
        # Per-request unique ID — useful for correlating logs with server traces
        corr_id = str(uuid.uuid4())
        extra_headers = {"X-Correlation-Id": corr_id, "X-Request-Id": corr_id}
        if "headers" in kwargs:
            kwargs["headers"] = {**extra_headers, **kwargs["headers"]}
        else:
            kwargs["headers"] = extra_headers

        logger.debug(f"API Request: {method} {path} corr_id={corr_id}", params=kwargs.get("params"))

        try:
            response = await self.client.request(method, path, **kwargs)

            # Check for non-2xx status codes to trigger retry via exception
            if response.status_code >= 500:
                response.raise_for_status()

            return response

        except httpx.HTTPError as e:
            logger.warning(f"API Request Failed: {method} {path}", status_code=getattr(e, 'response', None))
            raise e

    async def close(self):
        await self.client.aclose()
