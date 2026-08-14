
import asyncio
from core.database.postgres import AsyncSessionLocal
from database.models.reservation import ReservationTask
from sqlalchemy import select

async def check():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(ReservationTask))
        tasks = res.scalars().all()
        print(f"TOTAL TASKS: {len(tasks)}")
        for t in tasks:
            print(f"ID: {t.id} | Status: {t.status} | Event: {t.event_slug}")

if __name__ == "__main__":
    asyncio.run(check())
