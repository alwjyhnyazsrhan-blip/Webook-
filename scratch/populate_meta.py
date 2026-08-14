
import asyncio
import sys
import os
import json
from datetime import datetime, timezone
from sqlalchemy import select

# Add project root to sys.path
sys.path.append(os.getcwd())

from core.database.postgres import AsyncSessionLocal
from database.models.discovery import LiveEvent

async def populate_metadata():
    print("--- POPULATING SEATMAP METADATA ---")
    async with AsyncSessionLocal() as db:
        stmt = select(LiveEvent)
        events = (await db.execute(stmt)).scalars().all()
        
        count = 0
        for event in events:
            if not event.metadata_json:
                continue
                
            data = event.metadata_json
            if isinstance(data, str):
                data = json.loads(data)
                
            seats_io = data.get("seats_io", {})
            if isinstance(seats_io, dict):
                event.chart_key = seats_io.get("chart_key") or event.chart_key
                event.event_key = seats_io.get("event_key") or event.event_key
                event.workspace_key = seats_io.get("workspace_key") or event.workspace_key
            
            event.seats_provider = data.get("seats_provider") or event.seats_provider
            event.interactive_map_url = f"https://webook.com/ar/events/{event.slug}/book"
            event.last_verified_at = datetime.now(timezone.utc)
            count += 1
            
        await db.commit()
        print(f"Updated {count} events.")

if __name__ == "__main__":
    asyncio.run(populate_metadata())

