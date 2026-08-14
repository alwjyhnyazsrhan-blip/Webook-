import asyncio
from services.discovery.engine import DiscoveryEngine
from core.database.postgres import AsyncSessionLocal
from database.models.discovery import LiveEvent
from sqlalchemy import select, func

async def trigger_full_parity_sync():
    engine = DiscoveryEngine()
    
    print("\U0001f680 PHASE 1: SITEMAP DISCOVERY (NOW WITH ZONES)")
    async with AsyncSessionLocal() as db:
        new_shells = await engine._sync_from_sitemap(db)
        print(f"ï¿½ Discovered {new_shells} NEW shells from sitemaps.")
    
    print("\n\U0001f4a7 PHASE 2: DEEP HYDRATION (WITH FALLBACK PREFIXES)")
    # Reset attempts for FAILED events so they try the new fallback logic
    async with AsyncSessionLocal() as db:
        from sqlalchemy import update
        await db.execute(update(LiveEvent).where(LiveEvent.hydration_status == 'FAILED').values(hydration_attempts=0))
        await db.commit()
        print("ï¿½ Reset failed hydration attempts to retry with new logic.")

    stats = await engine.hydrate_all(batch_size=200, concurrency=3)
    print(f"ï¿½ Hydration Stats: {stats}")
    
    async with AsyncSessionLocal() as db:
        ready = (await db.execute(select(func.count(LiveEvent.id)).where(LiveEvent.hydration_status == 'READY'))).scalar()
        total = (await db.execute(select(func.count(LiveEvent.id)))).scalar()
        print(f"\U0001f3c1 FINAL STATUS: {ready}/{total} events are READY for the bot.")

if __name__ == "__main__":
    asyncio.run(trigger_full_parity_sync())

