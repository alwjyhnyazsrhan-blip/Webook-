from typing import Dict, Any, List, Optional
import asyncio
import time
from core.logging.logger import logger
from modules.auth.client import WebookAuthClient
from modules.sniper.scorer import SeatScorer
from core.network.client import BaseAPIClient
from core.network.endpoints import WebookEndpoints
from database.models.reservation import AuthSession
from apps.api.middleware.metrics import REQUEST_COUNT, REQUEST_LATENCY

from modules.webook.client import WebookApiClient
from database.models.reservation import AuthSession

class SniperEngine:
    """
    The Ultimate Sniper Engine.
    Fully connected to real Webook API with Section Discovery and Checkout Link Generation.
    """
    def __init__(self, session: AuthSession):
        self.api = WebookApiClient(
            bearer_token=session.bearer_token,
            proxy=session.proxy_url,
            user_agent=session.user_agent
        )
        self.scorer = SeatScorer()
        self.session = session

    async def get_sections(self, event_slug: str) -> List[Dict[str, Any]]:
        """Fetches map blocks/sections for targeted sniping."""
        try:
            response = await self.api.request("GET", f"/events/{event_slug}/sections")
            return response.json().get("data", [])
        except Exception as e:
            logger.error(f"Failed to fetch sections for {event_slug}", error=str(e))
            return []

    async def execute_reservation(self, event_slug: str, seat_count: int, category: str = None, zone: str = None) -> Dict[str, Any]:
        """
        Attack Mode: Targeted block-level sniping.
        """
        logger.info(f"Sniper Engine: STARTING TARGETED ATTACK on {event_slug} (Category: {category}, Zone: {zone})")
        
        attempts = 0
        while True:
            attempts += 1
            start_time = time.perf_counter()
            
            try:
                # 1. Fetch Availability
                # We use the hardened client's get_event_tickets or availability endpoint
                availability_data = await self.api.get_event_availability(event_slug)
                
                # 2. Scorer (Targeted by Category and Zone)
                selected_seats = self.scorer.score_seats(
                    availability_data.get("data", []) if isinstance(availability_data, dict) else [], 
                    seat_count,
                    category=category
                )
                
                if not selected_seats:
                    await asyncio.sleep(0.1)
                    continue
                
                # 3. Modern Checkout (Seated Flow)
                # We first need the event_id for the checkout payload
                # We can try to get it from the availability data or metadata
                event_id = availability_data.get("event_id") or availability_data.get("id")
                
                # If we don't have event_id, we might need a quick detail fetch
                if not event_id:
                    detail = await self.api.get_event_detail(event_slug)
                    event_id = detail.get("data", {}).get("id") if isinstance(detail, dict) else None
                
                if not event_id:
                    logger.error(f"SniperEngine: Could not resolve event_id for {event_slug}")
                    await asyncio.sleep(1.0)
                    continue

                checkout_resp = await self.api.checkout_seated(
                    slug=event_slug,
                    seats=selected_seats,
                    event_id=event_id
                )
                
                status_code = checkout_resp.get("_http_status", 0)
                if status_code in [200, 201]:
                    # SUCCESS: Obtain the hold/reservation ID from response
                    # Response varies: sometimes it's {'id': '...'}, sometimes {'data': {'id': '...'}}
                    res_id = checkout_resp.get("id") or checkout_resp.get("data", {}).get("id")
                    if res_id:
                        checkout_url = f"https://webook.com/en/checkout/{res_id}"
                        checkout_resp["id"] = res_id
                        checkout_resp["checkout_url"] = checkout_url
                        logger.info(f"SniperEngine: SNIPED (Seated)! Checkout: {checkout_url}")
                        return checkout_resp
                
                logger.warning(f"SniperEngine: Checkout attempt failed (Status: {status_code}) | {checkout_resp.get('message')}")
                await asyncio.sleep(0.2)

            except Exception as e:
                logger.error(f"Attack Mode Exception", error=str(e))
                await asyncio.sleep(0.5)

    async def release_hold(self, hold_id: str, event_slug: str) -> bool:
        response = await self.api.release_reservation(slug=event_slug, reservation_id=hold_id)
        return response.get("_http_status") in [200, 204]
