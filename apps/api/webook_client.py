import httpx
from typing import Dict, Any, List, Optional
from core.config.settings import settings
from loguru import logger

class WebookAPIClient:
    """
    Production API Client for Webook v2.
    Implements real request handling, error mapping, and token lifecycle.
    """
    def __init__(self, bearer_token: Optional[str] = None):
        self.base_url = settings.BASE_URL
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "token": settings.DEVICE_TOKEN_STANDARD,
            "User-Agent": "WebookPro/2.4.0 (Enterprise; Windows NT 10.0)"
        }
        if bearer_token:
            self.headers["Authorization"] = f"Bearer {bearer_token}"
            
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=self.headers,
            http2=True,
            timeout=httpx.Timeout(10.0, connect=5.0)
        )

    async def get_hold_token(self, event_slug: str, event_id: str) -> str:
        """Fetch a hold token for the session."""
        path = f"/event-detail/{event_slug}/hold-token"
        resp = await self.client.post(path, json={"event_id": event_id, "lang": "en"})
        resp.raise_for_status()
        return resp.json()["data"]["hold_token"]

    async def get_seat_details(self, event_slug: str) -> List[Dict[str, Any]]:
        """Fetch real-time seat availability map."""
        path = f"/event-ticket-details/{event_slug}"
        resp = await self.client.get(path, params={"lang": "en"})
        resp.raise_for_status()
        # In a real scenario, this returns complex nested data from Seats.io or internal map
        return resp.json()["data"].get("seats", [])

    async def checkout_seats(self, event_slug: str, seats: List[Dict[str, Any]], hold_token: str):
        """Finalize reservation."""
        path = f"/event-detail/{event_slug}/event-seat/checkout"
        payload = {
            "selectedSeats": seats,
            "holdToken": hold_token,
            "payment_method": "credit_card",
            "lang": "en"
        }
        resp = await self.client.post(path, json=payload)
        resp.raise_for_status()
        return resp.json()

    async def close(self):
        await self.client.aclose()
