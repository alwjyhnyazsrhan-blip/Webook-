import asyncio
from core.database.postgres import AsyncSessionLocal
from database.models.discovery import LiveEvent
from sqlalchemy import select

async def run():
    async with AsyncSessionLocal() as db:
        evs = (await db.execute(select(LiveEvent).where(LiveEvent.hydration_status == 'FAILED'))).scalars().all()
        print(f"FAILED HYDRATIONS ({len(evs)}):")
        for ev in evs[:20]:
            print(f" - {ev.slug}: {ev.last_hydration_error}")

if __name__ == "__main__":
    asyncio.run(run())

