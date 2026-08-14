import asyncio
from core.database.postgres import AsyncSessionLocal
from database.models.discovery import LiveEvent
from sqlalchemy import select
from datetime import datetime, timezone

async def fix_statuses():
    async with AsyncSessionLocal() as db:
        stmt = select(LiveEvent).where(LiveEvent.hydration_status == "READY")
        events = (await db.execute(stmt)).scalars().all()
        count = 0
        for ev in events:
            data = ev.metadata_json
            if not data: continue
            
            # Update starts_at
            start_ts = data.get("start_date_time") or data.get("startDate")
            if start_ts:
                try:
                    ev.starts_at = datetime.fromtimestamp(int(start_ts), tz=timezone.utc)
                except Exception: pass
            
            # Update status
            is_soldout = data.get("is_soldout") or data.get("is_sold_out") or data.get("sold_out")
            tickets = data.get("event_tickets") or data.get("ticket_packages") or []
            
            if is_soldout or (data.get("status") == "past") or (not tickets and data.get("status") != "upcoming"):
                ev.status = "SOLD_OUT"
            else:
                ev.status = "AVAILABLE"
            count += 1
        
        await db.commit()
        print(f"Fixed {count} event statuses in DB")

asyncio.run(fix_statuses())
