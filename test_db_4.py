import asyncio
import json
from core.database.postgres import AsyncSessionLocal
from database.models.discovery import LiveEvent
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as db:
        stmt = select(LiveEvent)
        res = await db.execute(stmt)
        for e in res.scalars().all():
            meta = e.metadata_json if e.metadata_json else {}
            tickets = meta.get("event_tickets") or meta.get("ticket_packages") or meta.get("tickets") or []
            if tickets:
                print(f"{e.slug} has {len(tickets)} tickets. Ticket 1 title: {tickets[0].get('title', 'N/A')}, price: {tickets[0].get('price', 'N/A')}")
            else:
                pass # print(f"{e.slug} has 0 tickets")

asyncio.run(main())
