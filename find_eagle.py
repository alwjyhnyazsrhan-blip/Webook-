import asyncio
from core.database.postgres import AsyncSessionLocal
from database.models.discovery import LiveEvent
from sqlalchemy import select

async def find_eagle():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(LiveEvent).where(LiveEvent.eagle_eye_image != None).limit(5))
        events = res.scalars().all()
        for e in events:
            print(f"TITLE:{e.title_ar}|EAGLE:{e.eagle_eye_image}")

if __name__ == "__main__":
    asyncio.run(find_eagle())
