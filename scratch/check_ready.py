import asyncio
from core.database.postgres import AsyncSessionLocal
from database.models.discovery import LiveEvent
from sqlalchemy import func, select

async def run():
    async with AsyncSessionLocal() as db:
        count = (await db.execute(select(func.count(LiveEvent.id)).where(LiveEvent.hydration_status == 'READY'))).scalar()
        print(f"TOTAL READY EVENTS: {count}")

if __name__ == "__main__":
    asyncio.run(run())

