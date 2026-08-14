import asyncio
from core.database.postgres import AsyncSessionLocal
from database.models.discovery import LiveEvent
from sqlalchemy import select

async def run():
    async with AsyncSessionLocal() as db:
        evs = (await db.execute(select(LiveEvent).where(LiveEvent.hydration_status == 'READY'))).scalars().all()
        print(f"READY EVENTS ({len(evs)}):")
        for ev in evs:
            print(f" - {ev.slug}")

if __name__ == "__main__":
    asyncio.run(run())

