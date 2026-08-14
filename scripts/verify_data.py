import asyncio
from sqlalchemy import select
from core.database.postgres import AsyncSessionLocal
from database.models.discovery import LiveEvent, Genre

async def check_data():
    async with AsyncSessionLocal() as db:
        genres = await db.execute(select(Genre))
        print(f"Total Genres: {len(genres.scalars().all())}")
        
        events = await db.execute(select(LiveEvent).limit(5))
        for ev in events.scalars().all():
            print(f"Event: {ev.title_ar} | Status: {ev.status} | Venue: {ev.venue_name}")

if __name__ == "__main__":
    asyncio.run(check_data())

