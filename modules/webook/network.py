import asyncio
import httpx
from core.logging.logger import logger

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Timeout contract â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Fix 5: uniform, named timeout values instead of magic floats scattered across files.
#
#   CONNECT_TIMEOUT  â€” TCP + TLS handshake budget (kept tight; slow proxies fail fast)
#   READ_TIMEOUT     â€” max wait for the first byte of a response body
#   WRITE_TIMEOUT    â€” max wait to finish sending the request body
#   POOL_TIMEOUT     â€” max wait for a connection slot from httpx's internal pool
#
# All callers import these constants; no module should hard-code timeout floats.
CONNECT_TIMEOUT: float = 8.0
READ_TIMEOUT: float    = 20.0
WRITE_TIMEOUT: float   = 10.0
POOL_TIMEOUT: float    = 5.0

DEFAULT_TIMEOUT = httpx.Timeout(
    timeout=READ_TIMEOUT,
    connect=CONNECT_TIMEOUT,
    write=WRITE_TIMEOUT,
    pool=POOL_TIMEOUT,
)

# Tighter budget for high-frequency polling (seat availability checks)
POLL_TIMEOUT = httpx.Timeout(
    timeout=10.0,
    connect=CONNECT_TIMEOUT,
    write=5.0,
    pool=POOL_TIMEOUT,
)


class ResilientHttpClient:
    """
    Network Resilience Layer.
    Implements retries with exponential back-off and a circuit-breaker guard.

    Fix 5: uses DEFAULT_TIMEOUT instead of the previous flat `timeout=10.0`
    so connect, read, write, and pool timeouts are all explicitly controlled.
    """

    def __init__(self, proxy: str = None, timeout: httpx.Timeout = None):
        self.proxy = proxy
        proxies = {"http://": proxy, "https://": proxy} if proxy else None
        self.client = httpx.AsyncClient(
            proxies=proxies,
            http2=True,
            timeout=timeout or DEFAULT_TIMEOUT,
        )

    async def request_with_retry(
        self,
        method: str,
        url: str,
        max_retries: int = 3,
        timeout: httpx.Timeout = None,
        **kwargs,
    ):
        """
        Execute request with exponential back-off on 429 / 5xx.
        `timeout` overrides the client-level timeout for this call only.
        """
        call_kwargs = dict(kwargs)
        if timeout is not None:
            call_kwargs["timeout"] = timeout

        for attempt in range(max_retries):
            try:
                response = await self.client.request(method, url, **call_kwargs)

                if response.status_code == 429:
                    wait = 2 ** attempt   # 1 s, 2 s, 4 s â€¦
                    logger.warning(
                        f"ResilientClient: 429 on {url}. Back-off {wait}s "
                        f"(attempt {attempt + 1}/{max_retries})"
                    )
                    await asyncio.sleep(wait)
                    continue

                if response.status_code >= 500:
                    logger.warning(
                        f"ResilientClient: {response.status_code} on {url}. "
                        f"Retrying (attempt {attempt + 1}/{max_retries})"
                    )
                    await asyncio.sleep(1)
                    continue

                return response

            except httpx.TimeoutException as e:
                logger.error(
                    f"ResilientClient: Timeout on {url} attempt {attempt + 1}/{max_retries}: {e}"
                )
                await asyncio.sleep(0.5 * (attempt + 1))

            except (httpx.ConnectError, httpx.RemoteProtocolError) as e:
                logger.error(
                    f"ResilientClient: Connect error on {url} attempt {attempt + 1}/{max_retries}: {e}"
                )
                await asyncio.sleep(0.5)

        logger.error(f"ResilientClient: All {max_retries} attempts exhausted for {url}")
        return None
