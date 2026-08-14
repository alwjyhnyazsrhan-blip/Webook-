import asyncio
from core.database.postgres import AsyncSessionLocal
from database.models.discovery import Genre, LiveEvent
from sqlalchemy import select

async def check():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Genre))
        genres = res.all()
        print(f"Total Genres in DB: {len(genres)}")
        
        res = await db.execute(select(LiveEvent))
        events = res.all()
        print(f"Total Events in DB: {len(events)}")

if __name__ == "__main__":
    asyncio.run(check())

