import asyncio
from core.database.postgres import AsyncSessionLocal
from database.models.discovery import LiveEvent
from sqlalchemy import select

async def list_all():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(LiveEvent.title_ar, LiveEvent.webook_id))
        rows = res.all()
        print(f"TOTAL_ROWS={len(rows)}")
        for row in rows:
            print(row)

if __name__ == "__main__":
    asyncio.run(list_all())

