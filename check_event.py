import asyncio
from core.database.postgres import AsyncSessionLocal
from database.models.discovery import LiveEvent
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as db:
        # Searching for the Taawoun vs Riyadh match found in browser
        stmt = select(LiveEvent).where(LiveEvent.title_ar.like("%\u0627\u0644\u062a\u0639\u0627\u0648\u0646%\u0627\u0644\u0631\u064a\u0627\u0636%"))
        event = (await db.execute(stmt)).scalar_one_or_none()
        if event:
            print(f"Found: {event.title_ar} | Status: {event.status} | Hydration: {event.hydration_status}")
        else:
            print("Event not found in bot DB")

asyncio.run(main())
