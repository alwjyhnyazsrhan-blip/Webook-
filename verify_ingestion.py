import asyncio
from services.discovery.engine import DiscoveryEngine
from core.database.postgres import AsyncSessionLocal
from database.models.discovery import LiveEvent, Genre
from sqlalchemy import select, func

async def run_sync():
    engine = DiscoveryEngine()
    print("Running Exhaustive Discovery...")
    count = await engine.sync_all()
    print(f"Discovery Complete. Total Shells: {count}")

    async with AsyncSessionLocal() as db:
        # Check Genres
        res = await db.execute(select(func.count(Genre.id)))
        genre_count = res.scalar()
        print(f"Genres in DB: {genre_count}")

        # Check Events
        res = await db.execute(select(func.count(LiveEvent.id)))
        event_count = res.scalar()
        print(f"Events in DB: {event_count}")

        # Check Statuses
        res = await db.execute(select(LiveEvent.hydration_status, func.count(LiveEvent.id)).group_by(LiveEvent.hydration_status))
        for status, c in res.all():
            print(f"Status {status}: {c}")

if __name__ == "__main__":
    asyncio.run(run_sync())

