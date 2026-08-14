import asyncio
import json
from core.database.postgres import AsyncSessionLocal
from database.models.discovery import LiveEvent
from sqlalchemy import select

async def check_categories():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(LiveEvent).where(LiveEvent.title_ar.like('%\u0627\u0644\u062e\u0644\u0648\u062f%')).limit(1))
        e = res.scalar_one_or_none()
        if e:
            print(f"TITLE: {e.title_ar}")
            print(f"STATUS: {e.status}")
            meta = e.metadata_json or {}
            tickets = meta.get("event_tickets") or meta.get("ticket_packages") or []
            print(f"CATEGORIES_COUNT: {len(tickets)}")
            for t in tickets:
                print(f"  CAT: {t.get('title') or t.get('name')} | PRICE: {t.get('price')} | REMAINING: {t.get('remaining')}")
        else:
            print("NONE")

if __name__ == "__main__":
    asyncio.run(check_categories())
