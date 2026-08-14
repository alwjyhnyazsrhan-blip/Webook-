import asyncio
from core.database.postgres import AsyncSessionLocal
from database.models.discovery import LiveEvent
from sqlalchemy import select, or_

async def find_any_map():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(LiveEvent).where(
            or_(
                LiveEvent.eagle_eye_image != None,
                LiveEvent.stadium_map_url != None,
                LiveEvent.seat_map_image != None
            )
        ).limit(10))
        events = res.scalars().all()
        for e in events:
            print(f"TITLE:{e.title_ar}")
            print(f"  EAGLE: {e.eagle_eye_image}")
            print(f"  STADIUM: {e.stadium_map_url}")
            print(f"  SEATMAP: {e.seat_map_image}")

if __name__ == "__main__":
    asyncio.run(find_any_map())
