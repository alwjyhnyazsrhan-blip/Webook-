import asyncio
import json
from core.database.postgres import AsyncSessionLocal
from database.models.discovery import LiveEvent
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as db:
        stmt = select(LiveEvent).where(LiveEvent.slug == "spl-week-34-al-hazem-vs-al-taawoun-3710")
        event = (await db.execute(stmt)).scalar_one_or_none()
        if event:
            meta = event.metadata_json if event.metadata_json else {}
            tickets = meta.get("event_tickets") or meta.get("ticket_packages") or meta.get("tickets") or []
            print(json.dumps(tickets, ensure_ascii=False, indent=2))
        else:
            print("Event not found")

asyncio.run(main())
