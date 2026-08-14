
import asyncio
import sys
import os
import json
from datetime import datetime, timezone, timedelta

# Add project root to sys.path
sys.path.append(os.getcwd())

from core.database.postgres import AsyncSessionLocal
from database.models.discovery import LiveEvent

async def inject_test_event():
    print("--- INJECTING TEST EVENT ---")
    async with AsyncSessionLocal() as db:
        test_event = LiveEvent(
            webook_id="test-123",
            title_ar="ÙØ¹Ø§ÙÙØ© ØªØ¬Ø±ÙØ¨ÙØ© ÙØ¹ ÙØ®Ø·Ø·",
            slug="test-event-with-map",
            status="AVAILABLE",
            venue_name="Stadiuim Test",
            image_url="https://webook.com/promo_poster.png",
            seats_provider="seats_io",
            chart_key="test-chart-key",
            event_key="test-event-key",
            workspace_key="test-workspace-key",
            interactive_map_url="https://webook.com/ar/events/test-event-with-map/book",
            last_verified_at=datetime.now(timezone.utc),
            metadata_json={
                "seats_io": {
                    "chart_key": "test-chart-key",
                    "event_key": "test-event-key",
                    "preview_3_1": "https://webook.com/seatmap_preview.jpg"
                }
            },
            starts_at=datetime.now(timezone.utc) + timedelta(days=1)
        )
        db.add(test_event)
        await db.commit()
        print(f"Injected test event with ID: {test_event.id}")

if __name__ == "__main__":
    asyncio.run(inject_test_event())
