import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/.."))

from core.database.postgres import AsyncSessionLocal
from database.models.discovery import LiveEvent
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as db:
        stmt = select(LiveEvent)
        res = await db.execute(stmt)
        events = res.scalars().all()
        print(f"Total events in database: {len(events)}")
        for e in events:
            if "فروسية" in (e.title_ar or "") or "polo" in (e.slug or "") or "polo" in (e.title_en or "").lower():
                print(f"ID: {e.id} | Slug: {e.slug} | Title: {e.title_ar} | Status: {e.status}")

if __name__ == "__main__":
    asyncio.run(main())
