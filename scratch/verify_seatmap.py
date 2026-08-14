
import asyncio
import sys
import os
from datetime import datetime, timezone
from sqlalchemy import select
from unittest.mock import AsyncMock, MagicMock

# Add project root to sys.path
sys.path.append(os.getcwd())

from core.database.postgres import AsyncSessionLocal
from database.models.discovery import LiveEvent
from apps.bot.handlers import handle_view_chart, _seatmap_payload

def log(msg):
    with open("scratch/verify_output.txt", "a", encoding="utf-8") as f:
        f.write(f"{msg}\n")
    print(msg)

async def verify_seatmap_flow():
    log("--- SEATMAP FLOW VERIFICATION ---")
    
    # 1. Check DB for an event with seatmap data
    async with AsyncSessionLocal() as db:
        stmt = select(LiveEvent).where(LiveEvent.slug == "test-no-img-event")
        event = (await db.execute(stmt)).scalar_one_or_none()
        
        if not event:
            print("[WARN] No event with chart_key found. Checking metadata_json...")
            stmt = select(LiveEvent).limit(5)
            events = (await db.execute(stmt)).scalars().all()
            for e in events:
                if e.metadata_json and "seats_io" in e.metadata_json:
                    event = e
                    print(f"[INFO] Found event via metadata: {e.slug}")
                    break
        
        if not event:
            print("[ERROR] No suitable event found for testing.")
            return

    log(f"[TEST] Targeted Event: {event.slug}")
    
    # 2. Test Payload Extraction Logic
    payload = _seatmap_payload(event)
    log(f"[TEST] Payload Keys: {list(payload.keys())}")
    log(f"[TEST] Provider: {payload['provider']}")
    log(f"[TEST] Image Present: {bool(payload['static_image'])}")
    log(f"[TEST] Keys Present: {bool(payload['chart_key'])} / {bool(payload['event_key'])}")
    
    # 3. Simulate handle_view_chart
    mock_callback = AsyncMock()
    mock_callback.data = f"v_ch:{event.id}"
    mock_callback.message = AsyncMock()
    mock_callback.message.answer_photo = AsyncMock()
    mock_callback.message.edit_text = AsyncMock()
    mock_callback.answer = AsyncMock()
    
    log("[TEST] Executing handle_view_chart...")
    await handle_view_chart(mock_callback)
    
    # 4. Inspect Results (Mocks)
    if mock_callback.message.answer_photo.called:
        log("[SUCCESS] Static image path triggered.")
        args, kwargs = mock_callback.message.answer_photo.call_args
        log(f"[TRACE] Image URL: {kwargs.get('photo', 'N/A')[:50]}...")
    elif mock_callback.message.edit_text.called:
        log("[SUCCESS] Interactive URL path triggered.")
        args, kwargs = mock_callback.message.edit_text.call_args
        log(f"[TRACE] Text: {args[0][:100]}...")
    else:
        log("[INFO] Fallback/Error path triggered.")

if __name__ == "__main__":
    asyncio.run(verify_seatmap_flow())

