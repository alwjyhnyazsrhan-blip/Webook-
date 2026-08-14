import asyncio
import sys
import io

# Force UTF-8 for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from core.database.postgres import AsyncSessionLocal
from database.models.discovery import LiveEvent
from sqlalchemy import select

async def check_event():
    async with AsyncSessionLocal() as db:
        stmt = select(LiveEvent).where(LiveEvent.slug == "riyadh-ettifaq")
        ev = (await db.execute(stmt)).scalar_one_or_none()
        if ev:
            print(f"Event: {ev.title_ar} ({ev.slug})")
            print(f"Status: {ev.status}")
            print(f"Hydration Status: {ev.hydration_status}")
            print(f"Genre ID: {ev.genre_id}")
            print(f"Metadata Status: {ev.metadata_json.get('status') if ev.metadata_json else 'N/A'}")
        else:
            print("Event not found in DB")

if __name__ == "__main__":
    asyncio.run(check_event())
