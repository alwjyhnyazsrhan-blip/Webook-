import asyncio
from core.database.postgres import AsyncSessionLocal
from database.models.discovery import LiveEvent
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as db:
        # Get visible events just like the bot does
        VISIBLE_STATUSES = ["READY", "DISCOVERED", "PARTIAL", "HYDRATING"]
        stmt = select(LiveEvent).where(
            LiveEvent.hydration_status.in_(VISIBLE_STATUSES)
        ).where(LiveEvent.status != "GHOST").order_by(LiveEvent.starts_at.asc()).limit(5)
        
        res = await db.execute(stmt)
        for e in res.scalars().all():
            print(f"Slug: {e.slug}, Starts: {e.starts_at}, Hydration: {e.hydration_status}")

asyncio.run(main())
