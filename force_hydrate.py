import asyncio
from services.discovery.engine import DiscoveryEngine
from core.database.postgres import AsyncSessionLocal
from database.models.discovery import LiveEvent
from modules.webook.client import WebookApiClient
from sqlalchemy import select

async def force_hydrate():
    slug = "spl-week-34-al-hazem-vs-al-taawoun-3710"
    discovery = DiscoveryEngine()
    api_client = WebookApiClient()
    async with AsyncSessionLocal() as db:
        stmt = select(LiveEvent).where(LiveEvent.slug == slug)
        event = (await db.execute(stmt)).scalar_one_or_none()
        if not event:
            print("Event not found")
            return
        
        print(f"Hydrating {slug}...")
        success = await discovery._hydrate_event(db, event, client=api_client)
        await db.commit()
        print(f"Success: {success}")
        
        # Verify
        await db.refresh(event)
        tickets = event.metadata_json.get("event_tickets") or event.metadata_json.get("ticket_packages") or []
        print(f"Tickets in DB now: {len(tickets)}")
        for t in tickets:
            print(f"  - {t.get('title')} (ID: {t.get('_id') or t.get('id')})")

if __name__ == "__main__":
    asyncio.run(force_hydrate())
