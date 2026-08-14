import asyncio
from core.database.postgres import AsyncSessionLocal
from database.models.discovery import LiveEvent
from sqlalchemy import select, func

async def check_slugs():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(LiveEvent.slug, func.length(LiveEvent.slug)).order_by(func.length(LiveEvent.slug).desc()).limit(10))
        for row in res.all():
            print(f"SLUG={row[0]} | LEN={row[1]}")

if __name__ == "__main__":
    asyncio.run(check_slugs())

