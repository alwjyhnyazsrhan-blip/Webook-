import asyncio
from core.database.postgres import AsyncSessionLocal
from database.models.discovery import LiveEvent
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as db:
        stmt = select(LiveEvent).order_by(LiveEvent.starts_at.asc()).limit(5)
        res = await db.execute(stmt)
        for e in res.scalars().all():
            print(e.slug, e.starts_at)

asyncio.run(main())
