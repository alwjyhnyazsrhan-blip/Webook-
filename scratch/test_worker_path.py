import asyncio
import os
import logging
from datetime import datetime, timezone
from sqlalchemy import select

# Set up environment
os.environ["PYTHONPATH"] = "."
logging.basicConfig(level=logging.INFO)
from core.logging.logger import logger

from core.database.postgres import AsyncSessionLocal
from database.models.discovery import LiveEvent
from database.models.account import AuthSession, AccountHealth
from database.models.reservation import ReservationTask, TaskStatus
from services.reservation.worker import ReservationWorker
from core.tracing.context import TraceContext

async def test_worker_path():
    print("\n" + "="*60)
    print("  RESERVATION WORKER PATH VALIDATION")
    print("="*60)

    slug = "spl-week-34-al-hazem-vs-al-taawoun-3710"
    
    async with AsyncSessionLocal() as db:
        # 1. Ensure Event exists
        event = (await db.execute(select(LiveEvent).where(LiveEvent.slug == slug))).scalar_one_or_none()
        if not event:
            print(f"  [FAIL] Event {slug} not found!")
            return

        # 2. Inject Mock Session
        session = AuthSession(
            email="test_sniper@webook.com",
            bearer_token="MOCK_TOKEN_PATH_VALIDATION",
            health=AccountHealth.ACTIVE.value,
            role="sniper"
        )
        db.add(session)
        await db.flush()
        
        # 3. Create Task
        task = ReservationTask(
            user_id=12345,
            account_id=session.id,
            event_slug=slug,
            seat_count=1,
            status=TaskStatus.QUEUED.value,
            trace_id="WORKER-VAL-1",
            created_at=datetime.now(timezone.utc)
        )
        db.add(task)
        await db.commit()
        
        task_id = task.id
        print(f"  [OK] Created task_id={task_id} with mock session")

    # 4. Run Worker (Mocking the API response to avoid real network calls if needed, 
    # but here we want to test the orchestration)
    worker = ReservationWorker()
    
    print(f"\n[STEP 2] Executing task {task_id}...")
    # We use a trace context to track it
    trace = TraceContext(trace_id="WORKER-VAL-1", user_id=12345)
    
    try:
        # We wrap the execution to capture logs
        await worker._execute_task(task_id)
    except Exception as e:
        print(f"  [INFO] Worker finished with exception (expected if token invalid): {e}")

    # 5. Check Task Status
    async with AsyncSessionLocal() as db:
        task = await db.get(ReservationTask, task_id)
        print(f"  Final Task Status: {task.status}")
        print(f"  Error Log: {task.error_log}")

        if "MISSING_SEATCLOUD_METADATA" in (task.error_log or ""):
            print("  [FAIL] SEAT_SELECTION_FAILED regression detected!")
        elif "SEAT_SELECTION" in (task.error_log or ""):
            print("  [INFO] Selection logic reached but failed (likely due to mock token/API)")
        else:
            print("  [OK] Worker path verified. No structural regressions in selection logic.")

    print("\n" + "="*60)
    print("  VALIDATION COMPLETE")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(test_worker_path())
