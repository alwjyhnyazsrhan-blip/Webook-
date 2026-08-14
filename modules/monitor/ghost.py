import asyncio
from typing import List, Set
from core.network.client import BaseAPIClient
from core.logging.logger import logger
from apps.bot.main import bot
from core.config.settings import settings

class GhostMonitor:
    """
    The Ghost Monitor: Scans Webook Backend for hidden events 
    and membership reuirements before they go public.
    """
    def __init__(self):
        self.api = BaseAPIClient(base_url="https://api.webook.com")
        self.known_events: Set[str] = set()

    async def scan_for_new_events(self):
        """
        Polls the events list API to detect 'unlisted' or 'coming soon' tags.
        """
        logger.info("Ghost Monitor: Starting silent backend scan...")
        while True:
            try:
                # 1. Fetch internal events list
                # In reality, this would hit the API endpoint discovered via reverse engineering
                response = await self.api.request("GET", "/events/internal-list")
                events = response.json().get("data", [])
                
                for event in events:
                    slug = event.get("slug")
                    if slug not in self.known_events:
                        await self.notify_admin(event)
                        self.known_events.add(slug)
                
                # Check every 30 seconds for hidden drops
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error("Ghost Monitor Error", error=str(e))
                await asyncio.sleep(10)

    async def notify_admin(self, event: dict):
        """Sends a Telegram alert for early detection."""
        message = (
            " *Ghost Monitor: Early Detection!*\n\n"
            f"\U0001f4cd *Event:* {event.get('name')}\n"
            f"\U0001f517 *Slug:* `{event.get('slug')}`\n"
            f"\U0001f4b0 *Price From:* {event.get('min_price')} SAR\n"
            f"\U0001f512 *Reuirements:* {event.get('membership_reuired', 'None')}\n"
            "\n_Ready to Sniper? Use /reserve command now!_"
        )
        
        for admin_id in settings.admin_ids:
            try:
                await bot.send_message(admin_id, message, parse_mode="Markdown")
            except Exception as e:
                logger.error(f"Failed to send alert to {admin_id}", error=str(e))
