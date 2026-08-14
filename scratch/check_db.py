import asyncio
from core.database.postgres import AsyncSessionLocal
from database.models.discovery import LiveEvent
from sqlalchemy import select

async def check():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(LiveEvent))
        events = res.scalars().all()
        print(f"Found {len(events)} events")
        for e in events:
            print(f"ID: {e.id} | Title: {e.title_ar} | Status: {e.status} | Date: {e.starts_at}")

if __name__ == "__main__":
    asyncio.run(check())

