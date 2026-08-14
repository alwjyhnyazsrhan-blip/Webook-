import asyncio
import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/.."))

from core.database.postgres import AsyncSessionLocal
from database.models.discovery import LiveEvent
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as db:
        stmt = select(LiveEvent).where(LiveEvent.slug == "spl-week-34-al-kholood-vs-al-fateh-9190")
        event = (await db.execute(stmt)).scalar_one_or_none()
        if not event:
            print("Event not found in database!")
            return
        
        print(f"ID: {event.id}")
        print(f"Slug: {event.slug}")
        print(f"Title: {event.title_ar}")
        print(f"Status: {event.status}")
        print("Metadata JSON:")
        print(json.dumps(event.metadata_json or {}, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(main())
