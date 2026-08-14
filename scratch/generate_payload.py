import asyncio
import os
import json
import sys

# Fix for Windows Arabic printing
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

os.environ["PYTHONPATH"] = "."
from core.database.postgres import AsyncSessionLocal
from database.models.discovery import LiveEvent
from services.reservation.worker import ReservationWorker
from modules.webook.client import WebookApiClient
from modules.session.context import create_session_context, close_session_context, SessionState
from database.models.reservation import ReservationTask, TaskStatus
from datetime import datetime, timezone
from sqlalchemy import select

async def generate_payload():
    slug = "spl-week-32-al-kholood-vs-al-okhdood-9720"
    
    async with AsyncSessionLocal() as db:
        event = (await db.execute(select(LiveEvent).where(LiveEvent.slug == slug))).scalar_one_or_none()
        if not event:
            print(f"Event {slug} not found!")
            return

    ctx = await create_session_context(
        account_id="payload_test",
        event_slug=slug,
        flow_type="seated",
        proxy_config=None,
        fingerprint_headers={"User-Agent": "Mozilla/5.0"}
    )
    
    task = ReservationTask(
        user_id=123,
        event_slug=slug,
        seat_count=1,
        status=TaskStatus.QUEUED.value,
        trace_id=ctx.correlation_id,
        created_at=datetime.now(timezone.utc)
    )

    worker = ReservationWorker()
    client = WebookApiClient(session_ctx=ctx)
    
    from services.discovery.engine import DiscoveryEngine
    engine = DiscoveryEngine()
    detail = await engine.api.get_event_detail(slug)
    from apps.bot.handlers_v2.event_detail import extract_ticket_list
    tickets = extract_ticket_list(detail)
    
    # We'll use the first ticket (Silver)
    ticket = tickets[0]
    
    # Simulate the build
    best_seats = await worker._build_seatcloud_selection(
        client, ctx, task, detail, ticket
    )
    
    # Generate the final stringified payload that Webook expects
    # (The worker's _execute_task would do this)
    payload_str = json.dumps(best_seats, ensure_ascii=False)
    
    print("\n[CODE_GENERATED_PAYLOAD]")
    print(payload_str)
    
    await close_session_context(ctx)

if __name__ == "__main__":
    asyncio.run(generate_payload())
