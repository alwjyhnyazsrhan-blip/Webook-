import asyncio
import os
import sys

# Add current dir to path
sys.path.append(os.getcwd())

from core.database.postgres import AsyncSessionLocal
from database.models.discovery import LiveEvent
from sqlalchemy import select
from services.seatmap.renderer import render_seatmap_png

async def audit_seatmaps():
    print("--- SEATMAP AUDIT START ---")
    async with AsyncSessionLocal() as db:
        # 1. Find an event with a chart key
        stmt = select(LiveEvent).where(LiveEvent.chart_key != None).limit(5)
        result = await db.execute(stmt)
        events = result.scalars().all()
        
        if not events:
            print("No events with chart_key found. Checking for any event...")
            stmt = select(LiveEvent).limit(5)
            result = await db.execute(stmt)
            events = result.scalars().all()

        if not events:
            print("CRITICAL: No events found in database.")
            return

        for ev in events:
            print(f"Event: {ev.title_ar} | Slug: {ev.slug}")
            print(f"  Chart Key: {ev.chart_key}")
            print(f"  Eagle Eye: {ev.eagle_eye_image}")
            
            if ev.eagle_eye_image:
                print(f"  RESULT: Real Seat Chart (Eagle View) exists at {ev.eagle_eye_image}")
            
            if ev.chart_key:
                print(f"  ACTION: Attempting render...")
                try:
                    path = await render_seatmap_png(
                        slug=ev.slug,
                        chart_key=ev.chart_key,
                        event_key=ev.event_key,
                        workspace_key=ev.workspace_key
                    )
                    if path and os.path.exists(path):
                        print(f"  RESULT: Rendered PNG successfully at {path} (Size: {os.path.getsize(path)} bytes)")
                    else:
                        print(f"  RESULT: Rendering failed or returned no path.")
                except Exception as e:
                    print(f"  RESULT: Error during render: {e}")
            else:
                print(f"  RESULT: No chart_key available for rendering.")

if __name__ == "__main__":
    # Ensure DATABASE_URL is set correctly for local run
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///C:/Users/batoot/Downloads/webook_FIXED_v7/webook_v6/data/webook.db"
    asyncio.run(audit_seatmaps())
