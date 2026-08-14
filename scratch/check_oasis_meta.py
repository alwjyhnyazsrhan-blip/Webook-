import asyncio
import json
from core.database.postgres import AsyncSessionLocal
from database.models.discovery import LiveEvent
from sqlalchemy import select

async def run():
    async with AsyncSessionLocal() as db:
        ev = (await db.execute(select(LiveEvent).where(LiveEvent.slug == 'oasis-rs-24'))).scalar_one_or_none()
        if ev:
            meta = ev.metadata_json
            print(f"METADATA FOR oasis-rs-24:")
            print(f"  Keys: {list(meta.keys())}")
            if 'seasons' in meta:
                print(f"  Seasons Found: {len(meta['seasons'])}")
                for s in meta['seasons']:
                    print(f"    - {s.get('title')} ({s.get('slug')})")

if __name__ == "__main__":
    asyncio.run(run())

