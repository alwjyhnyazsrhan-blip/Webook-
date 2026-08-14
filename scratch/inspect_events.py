import asyncio
import os
import sys
sys.path.append(os.getcwd())

from core.database.postgres import AsyncSessionLocal
from database.models.discovery import LiveEvent
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(LiveEvent).limit(10))
        events = res.scalars().all()
        for e in events:
            print(f"ID: {e.id} | Slug: {e.slug} | Status: {e.status}")

if __name__ == "__main__":
    asyncio.run(main())
