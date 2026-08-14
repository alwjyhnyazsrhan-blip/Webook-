import asyncio
import os
import sys

# Add project root to sys.path
sys.path.append(os.getcwd())

async def run_sync():
    from services.discovery.engine import DiscoveryEngine
    from core.database.postgres import AsyncSessionLocal
    from database.models.discovery import LiveEvent, Genre
    from sqlalchemy import update, delete
    
    print("Resetting genres to re-categorize...")
    async with AsyncSessionLocal() as db:
        # We don't delete events, just reset their genre_id to force re-categorization
        await db.execute(update(LiveEvent).values(genre_id=None))
        # Optional: delete old inactive genres
        # await db.execute(delete(Genre).where(Genre.is_active == False))
        await db.commit()
    
    engine = DiscoveryEngine()
    print("Starting full sync...")
    try:
        count = await engine.sync_all()
        print(f"Sync complete! Discovered {count} events.")
    except Exception as e:
        print(f"Sync failed with error: {e}")
        # Even if it failed, some events should be categorized now

if __name__ == '__main__':
    asyncio.run(run_sync())
