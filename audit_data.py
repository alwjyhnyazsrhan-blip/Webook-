import asyncio
from core.database.postgres import AsyncSessionLocal
from database.models.discovery import LiveEvent
from sqlalchemy import select, func

async def audit():
    async with AsyncSessionLocal() as db:
        # 1. Distribution of hydration_status
        res = await db.execute(select(LiveEvent.hydration_status, func.count(LiveEvent.id)).group_by(LiveEvent.hydration_status))
        dist = res.all()
        print("\n--- HYDRATION STATUS DISTRIBUTION ---")
        if not dist:
            print("DB IS COMPLETELY EMPTY")
        for status, count in dist:
            print(f"{status}: {count}")

        # 2. Total Ready
        res = await db.execute(select(func.count(LiveEvent.id)).where(LiveEvent.hydration_status == 'READY'))
        ready_count = res.scalar()
        print(f"TOTAL READY: {ready_count}")

        # 3. Sample of Discovered but not Ready
        res = await db.execute(select(LiveEvent.slug, LiveEvent.hydration_status, LiveEvent.hydration_attempts, LiveEvent.last_hydration_error).limit(5))
        samples = res.all()
        print("\n--- SAMPLE EVENTS ---")
        for s in samples:
            print(f"Slug: {s.slug} | Status: {s.hydration_status} | Attempts: {s.hydration_attempts} | Error: {s.last_hydration_error}")

if __name__ == "__main__":
    asyncio.run(audit())

