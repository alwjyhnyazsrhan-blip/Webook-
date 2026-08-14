"""
WebookReservationEngine  (Fix 6)
=================================
Fix 6: The engine no longer instantiates its own ResilientHttpClient.
Instead, the caller passes in the httpx.AsyncClient from
ReservationSessionContext so every request in the chain shares the same
cookie jar, proxy, and fingerprint.

Old (broken):
    engine = WebookReservationEngine(proxy=proxy_url)
    # engine._network held a separate client â€” different cookies, identity drift

New (correct):
    engine = WebookReservationEngine(http_client=ctx.httpx_client)
    # engine uses ctx.httpx_client â€” same session, same cookies
"""

import asyncio
import httpx

from core.logging.logger import logger


class WebookReservationEngine:
    """
    The Core Sniper Logic.
    Parses live seat matrices and executes atomic hold requests.

    Parameters
    ----------
    http_client : httpx.AsyncClient
        The pinned client from ReservationSessionContext.  All requests
        go through this client so cookies and identity stay consistent.
    bearer_token : str
        Authenticated bearer token for the account.
    """

    def __init__(self, http_client: httpx.AsyncClient, bearer_token: str):
        # Fix 6: injected client â€” never create one internally
        self._client = http_client
        self._bearer_token = bearer_token

    async def find_and_hold_seats(
        self,
        event_id: str,
        category_id: str,
        count: int,
        max_retries: int = 3,
    ) -> dict:
        """
        Full execution trace: Fetch matrix â†’ parse adjacency â†’ request hold.

        Returns a result dict with keys:
          status : "SUCCESS" | "SEARCHING" | "FAILED"
          reason : short failure code (when status != SUCCESS)
          data   : hold response payload (when status == SUCCESS)
        """
        url = f"https://api.webook.com/events/{event_id}/availability?category={category_id}"

        for attempt in range(max_retries):
            try:
                matrix_resp = await self._client.get(url)
            except (httpx.TimeoutException, httpx.ConnectError) as e:
                logger.error(f"Engine: matrix fetch error attempt {attempt + 1}: {e}")
                await asyncio.sleep(0.5 * (attempt + 1))
                continue

            if matrix_resp.status_code == 429:
                await asyncio.sleep(2 ** attempt)
                continue

            if matrix_resp.status_code != 200:
                logger.warning(f"Engine: matrix fetch HTTP {matrix_resp.status_code}")
                return {"status": "FAILED", "reason": f"MATRIX_HTTP_{matrix_resp.status_code}"}

            matrix = matrix_resp.json()
            best_seats = self._find_contiguous_seats(matrix, count)

            if not best_seats:
                return {"status": "SEARCHING", "reason": "NO_CONTIGUOUS_SEATS_FOUND"}

            # Atomic hold
            hold_url = "https://api.webook.com/reservations/hold"
            payload = {
                "event_id": event_id,
                "seat_ids": [s["id"] for s in best_seats],
                "total_count": count,
            }
            headers = {"Authorization": f"Bearer {self._bearer_token}"}

            try:
                hold_resp = await self._client.post(hold_url, json=payload, headers=headers)
            except (httpx.TimeoutException, httpx.ConnectError) as e:
                logger.error(f"Engine: hold request error attempt {attempt + 1}: {e}")
                await asyncio.sleep(0.5 * (attempt + 1))
                continue

            if hold_resp.status_code in (200, 201):
                return {"status": "SUCCESS", "data": hold_resp.json()}

            if hold_resp.status_code == 409:
                # Race lost â€” seats taken between fetch and hold; retry
                await asyncio.sleep(0.2)
                continue

            return {"status": "FAILED", "reason": f"HOLD_HTTP_{hold_resp.status_code}"}

        return {"status": "FAILED", "reason": "MAX_RETRIES_EXHAUSTED"}

    def _find_contiguous_seats(self, matrix: dict, count: int):
        """
        Physical adjacency algorithm.
        Looks for sequential IDs in the same zone using a sliding window.
        """
        for zone in matrix.get("available_zones", []):
            seats = sorted(zone.get("seats", []), key=lambda x: x["id"])
            for i in range(len(seats) - count + 1):
                window = seats[i: i + count]
                if all(window[j]["id"] == window[0]["id"] + j for j in range(count)):
                    return window
        return None
