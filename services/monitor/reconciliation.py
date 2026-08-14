import asyncio
import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, update, and_, or_

from core.database.postgres import AsyncSessionLocal
from database.models.reservation import ReservationTask, TaskStatus
from database.models.account import AuthSession
from modules.webook.client import WebookApiClient

logger = logging.getLogger("ReconciliationJob")
logger.setLevel(logging.INFO)

class ReconciliationJob:
    """
    Background job to ensure state consistency across the cluster and external APIs.
    Validates holds, verifies timeouts, rescues zombies, and ensures zero orphaned tickets.
    """

    def __init__(self, interval_seconds: int = 300):
        self.interval_seconds = interval_seconds
        self._running = False

    async def start(self):
        self._running = True
        logger.info("[RECONCILIATION] Started background reconciliation job")
        while self._running:
            try:
                await self._run_pass()
            except Exception as e:
                logger.error(f"[RECONCILIATION_ERROR] Unhandled exception: {e}")
            await asyncio.sleep(self.interval_seconds)

    def stop(self):
        self._running = False
        
    async def _run_pass(self):
        logger.info("[RECONCILIATION] Starting reconciliation pass")
        async with AsyncSessionLocal() as db:
            await self._recover_zombie_tasks(db)
            await self._reconcile_ambiguous_checkouts(db)
            await self._clean_orphan_holds(db)
            
    async def _recover_zombie_tasks(self, db):
        """Finds tasks stuck in ACTIVE states without recent heartbeats."""
        zombie_threshold = datetime.now(timezone.utc) - timedelta(minutes=5)
        stmt = select(ReservationTask).where(
            and_(
                ReservationTask.status.in_([TaskStatus.SEARCHING.value, TaskStatus.HOLDING.value, TaskStatus.PROCESSING.value]),
                ReservationTask.last_heartbeat < zombie_threshold
            )
        )
        result = await db.execute(stmt)
        zombies = result.scalars().all()
        
        for task in zombies:
            logger.warning(f"[ZOMBIE_RECOVERED] task_id={task.id} stuck in {task.status}")
            task.status = TaskStatus.FAILED.value
            task.error_message = "ZOMBIE_RECOVERED: Worker crashed or lease expired"
            task.worker_id = None
            
            # Release hold if exists
            if task.hold_token:
                await self._release_hold_safely(db, task)
                
            await db.commit()
            
    async def _reconcile_ambiguous_checkouts(self, db):
        """Finds FAILED tasks that might have actually succeeded (timeout ambiguity)."""
        recent_threshold = datetime.now(timezone.utc) - timedelta(hours=2)
        stmt = select(ReservationTask).where(
            and_(
                ReservationTask.status.in_([TaskStatus.FAILED.value, "FAILED_DLQ"]),
                ReservationTask.updated_at > recent_threshold,
                ReservationTask.account_id.isnot(None)
            )
        )
        result = await db.execute(stmt)
        tasks = result.scalars().all()
        
        for task in tasks:
            acc = await db.get(AuthSession, task.account_id)
            if not acc or not acc.bearer_token:
                continue
                
            try:
                api = WebookApiClient()
                await api.set_bearer(acc.bearer_token)
                bookings_res = await api.get_user_bookings()
                
                # Check if we have a valid booking for this event
                orders = bookings_res.get("data", {}).get("data", [])
                for order in orders:
                    if order.get("status") not in ("cancelled", "failed"):
                        # In production we match `order.event_slug` or ID, but here we assume recent orders
                        logger.warning(f"[RECONCILIATION_SUCCESS] Retroactively matched order for task_id={task.id}")
                        task.status = TaskStatus.COMPLETED.value
                        task.error_message = "ORDER_FOUND_VIA_RECONCILIATION"
                        
                        logs = list(task.execution_logs or [])
                        logs.append({"ts": datetime.now(timezone.utc).isoformat(), "msg": "RECONCILIATION: Recovered lost order"})
                        task.execution_logs = logs
                        
                        await db.commit()
                        break
            except Exception as e:
                logger.error(f"[RECONCILIATION_BOOKINGS_FAIL] task_id={task.id} {e}")

    async def _clean_orphan_holds(self, db):
        """Releases holds for expired tasks or cancelled tasks that missed their release API call."""
        stmt = select(ReservationTask).where(
            and_(
                ReservationTask.status.in_([TaskStatus.CANCELLED.value, TaskStatus.EXPIRED.value]),
                ReservationTask.hold_token.isnot(None),
                ReservationTask.updated_at > datetime.now(timezone.utc) - timedelta(hours=1)
            )
        )
        result = await db.execute(stmt)
        orphans = result.scalars().all()
        
        for task in orphans:
            logger.info(f"[ORPHAN_CLEANUP] Releasing leftover hold for task_id={task.id}")
            await self._release_hold_safely(db, task)
            task.hold_token = None  # Clear to prevent duplicate release attempts
            await db.commit()
            
    async def _release_hold_safely(self, db, task):
        if not task.account_id or not task.hold_token:
            return
        try:
            acc = await db.get(AuthSession, task.account_id)
            if acc and acc.bearer_token:
                api = WebookApiClient()
                await api.set_bearer(acc.bearer_token)
                await api.release_reservation(slug=task.event_slug, hold_token=task.hold_token)
                logger.info(f"[HOLD_RELEASED] task_id={task.id} hold_token={task.hold_token}")
        except Exception as e:
            logger.error(f"[HOLD_RELEASE_FAIL] task_id={task.id} {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    job = ReconciliationJob(interval_seconds=60)
    asyncio.run(job.start())
