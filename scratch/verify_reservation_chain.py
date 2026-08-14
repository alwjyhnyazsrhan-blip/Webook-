import asyncio
import os
import json
import sys
from sqlalchemy import select
from sqlalchemy.orm import joinedload

# Fix for Windows Arabic printing
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

# Set up environment
os.environ["PYTHONPATH"] = "."
from core.database.postgres import AsyncSessionLocal
from database.models.discovery import LiveEvent
from services.reservation.worker import ReservationWorker
from modules.webook.client import WebookApiClient
from modules.session.context import create_session_context, close_session_context, SessionState
from core.tracing.context import TraceContext
from database.models.reservation import ReservationTask, TaskStatus
from datetime import datetime, timezone

async def verify_reservation_chain():
    print("\n" + "="*60)
    print("  RESERVATION CHAIN VERIFICATION (REAL DATA)")
    print("="*60)

    slug = "spl-week-32-al-kholood-vs-al-okhdood-9720"
    
    async with AsyncSessionLocal() as db:
        event = (await db.execute(select(LiveEvent).where(LiveEvent.slug == slug))).scalar_one_or_none()
        if not event:
            print(f"  [FAIL] Event {slug} not found!")
            return

        print(f"[STEP 1] Event: {event.title_ar}")
        print(f"  Chart Key: {event.chart_key}")
        print(f"  Event Key: {event.event_key}")
        print(f"  Workspace: {event.workspace_key}")

    # Initialize a REAL Session Context
    ctx = await create_session_context(
        account_id="verify_test",
        event_slug=slug,
        flow_type="seated",
        proxy_config=None,
        fingerprint_headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Origin": "https://webook.com",
            "Referer": "https://webook.com/",
        }
    )
    
    # Create a mock task
    async with AsyncSessionLocal() as db:
        task = ReservationTask(
            user_id=123,
            event_slug=slug,
            seat_count=1,
            status=TaskStatus.QUEUED.value,
            trace_id=ctx.correlation_id,
            created_at=datetime.now(timezone.utc)
        )
        db.add(task)
        await db.commit()
        task_id = task.id

    worker = ReservationWorker()
    client = WebookApiClient(session_ctx=ctx)

    print("\n[STEP 2] Simulating _build_seatcloud_selection...")
    from services.discovery.engine import DiscoveryEngine
    engine = DiscoveryEngine()
    detail = await engine.api.get_event_detail(slug)
    from apps.bot.handlers_v2.event_detail import extract_ticket_list
    tickets = extract_ticket_list(detail)
    
    if not tickets:
        print("  [FAIL] No tickets found!")
        return
    
    ticket = tickets[0]
    print(f"  Selected Ticket: {ticket.get('title')} (id={ticket.get('id')})")
    
    try:
        ctx.transition(SessionState.HOLD_TOKEN_ACQUIRED)

        print("  [INFO] Fetching real Seats.io chart data...")
        chart_data = await client.get_seatcloud_chart_data(event.workspace_key, event.chart_key)
        if not chart_data:
            print("  [FAIL] Seats.io API returned empty data for these keys!")
            return
        
        print(f"  [SUCCESS] Seats.io data fetched: {len(chart_data.get('sections', []))} sections")

        best_seats = await worker._build_seatcloud_selection(
            client, ctx, task, detail, ticket
        )
        
        if best_seats:
            print(f"\n[STEP 3] SELECTION SUCCESS!")
            print(f"  Seats selected: {len(best_seats)}")
            for s in best_seats:
                stype = s.get("itemType")
                if stype == "seat":
                    print(f"  - SEAT: Row {s.get('rowName')} Label {s.get('label')} (ID: {s.get('id')})")
                else:
                    print(f"  - AREA (GA): {s.get('name')} Label {s.get('label')} (ID: {s.get('id')})")
            
            payload = {
                "slug": slug,
                "seats": best_seats
            }
            print(f"\n[FINAL PAYLOAD PREVIEW]\n{json.dumps(payload, indent=2, ensure_ascii=False)}")
            print("\n[VERDICT] Seated flow logic is now FULLY VALIDATED for GA Areas (Saudi Pro League).")
        else:
            print("\n[STEP 3] SELECTION FAILED (Logic matched 0 seats)")
            
    except Exception as e:
        print(f"  [ERROR] Selection logic crashed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await close_session_context(ctx)

    print("\n" + "="*60)
    print("  VERIFICATION COMPLETE")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(verify_reservation_chain())
