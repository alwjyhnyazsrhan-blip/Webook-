import asyncio
import os
from core.database.postgres import AsyncSessionLocal
from database.models.discovery import LiveEvent
from sqlalchemy import select
from services.seatmap.renderer import render_seatmap_png
from core.logging.logger import logger

async def test_seatmap():
    print("--- SEATMAP DIAGNOSTIC START ---")
    async with AsyncSessionLocal() as db:
        # Find events with seatmap metadata
        stmt = select(LiveEvent).where(LiveEvent.chart_key != None).limit(5)
        events = (await db.execute(stmt)).scalars().all()
        
        if not events:
            print("No events with chart_key found in DB. Trying any event...")
            stmt = select(LiveEvent).limit(5)
            events = (await db.execute(stmt)).scalars().all()
        
        if not events:
            print("NO EVENTS FOUND AT ALL IN DB.")
            return

        for event in events:
            print(f"Testing Event: {event.title_ar} (Slug: {event.slug})")
            print(f"  Chart Key: {event.chart_key}")
            print(f"  Eagle Eye Image: {event.eagle_eye_image}")
            
            # Attempt to render
            if event.chart_key:
                try:
                    # We need a hold token for real rendering often, but let's see if it works without or with dummy
                    path = await render_seatmap_png(
                        slug=event.slug,
                        provider=event.seats_provider or "seats_io",
                        chart_key=event.chart_key,
                        event_key=event.event_key,
                        workspace_key=event.workspace_key,
                        hold_token=None
                    )
                    if path and os.path.exists(path):
                        print(f"  SUCCESS: Rendered PNG at {path}")
                    else:
                        print(f"  FAILED: render_seatmap_png returned {path}")
                except Exception as e:
                    print(f"  ERROR Rendering: {e}")
            elif event.eagle_eye_image:
                print(f"  INFO: Has Eagle Eye URL: {event.eagle_eye_image}")
            else:
                print("  SKIP: No visual data available for this event.")

if __name__ == "__main__":
    asyncio.run(test_seatmap())
