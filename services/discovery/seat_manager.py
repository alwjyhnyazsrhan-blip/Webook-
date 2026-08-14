from core.database.postgres import AsyncSessionLocal
from database.models.discovery import SeatMapCache, LiveEvent
from modules.webook.engine import WebookReservationEngine
from sqlalchemy import select, update
from datetime import datetime, timezone
from core.logging.logger import logger

class SeatAvailabilityManager:
    """
    Live Seat Map Orchestrator. 
    Syncs real-time stadium availability into the fast-cache.
    """
    def __init__(self):
        self.engine = WebookReservationEngine()

    async def sync_event_availability(self, event_webook_id: str):
        """Live Sync of a specific event's seat map."""
        logger.info(f"Seat_Manager: Syncing availability for {event_webook_id}")
        
        # 1. Fetch real matrix from engine
        # In production, this calls the engine we built in Step 9 previously
        matrix = await self.engine.network.request_with_retry(
            "GET", f"https://api.webook.com/events/{event_webook_id}/availability"
        )
        
        if not matrix: return

        data = matrix.json()
        async with AsyncSessionLocal() as db:
            event_stmt = select(LiveEvent).where(LiveEvent.webook_id == event_webook_id)
            event = (await db.execute(event_stmt)).scalar_one()

            # 2. Update each section/category live
            for zone in data.get("available_zones", []):
                cache_stmt = select(SeatMapCache).where(
                    SeatMapCache.event_id == event.id,
                    SeatMapCache.section_id == zone['id']
                )
                cache = (await db.execute(cache_stmt)).scalar_one_or_none()
                
                if not cache:
                    cache = SeatMapCache(event_id=event.id, section_id=zone['id'])
                    db.add(cache)
                
                cache.category_name = zone.get('name')
                cache.available_seats = len([s for s in zone.get('seats', []) if s['status'] == 'AVAILABLE'])
                cache.price = zone.get('price')
                cache.is_sold_out = cache.available_seats == 0
                cache.last_refresh = datetime.now(timezone.utc)
            
            await db.commit()
            logger.info(f"Seat_Manager: Availability Synced for {event_webook_id}")

    async def get_live_seat_map(self, event_id: int):
        """Returns the synchronized live map for the UI."""
        async with AsyncSessionLocal() as db:
            stmt = select(SeatMapCache).where(SeatMapCache.event_id == event_id)
            result = await db.execute(stmt)
            return result.scalars().all()

