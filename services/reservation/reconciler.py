import asyncio
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, and_, or_, update
from core.database.postgres import AsyncSessionLocal
from database.models.reservation import ReservationTask, TaskStatus
from core.logging.logger import logger
from modules.webook.client import WebookApiClient
from database.repositories.account import AccountRepository

class ReconciliationWorker:
    """
    PHASE 2: Distributed Recovery & Zombie Mitigation.
    Detects and recovers from 'Zombie Holds' and stale execution states.
    """
    
    def __init__(self, check_interval: int = 300):
        self.check_interval = check_interval

    async def run(self):
        logger.info("ReconciliationWorker: Distributed recovery engine STARTED")
        while True:
            try:
                await self.reconcile_zombies()
            except Exception as e:
                logger.error(f"ReconciliationWorker: Cycle failed: {e}")
            await asyncio.sleep(self.check_interval)

    async def reconcile_zombies(self):
        """
        Scans for tasks in 'HOLDING' or 'SEARCHING' that have no heartbeat.
        Verifies real hold state with Webook API and reconciles.
        """
        stale_threshold = datetime.now(timezone.utc) - timedelta(seconds=120)
        
        async with AsyncSessionLocal() as db:
            # 1. Find stale 'HOLDING' or 'SEARCHING' tasks
            stmt = select(ReservationTask).where(
                and_(
                    ReservationTask.status.in_([TaskStatus.SEARCHING.value, TaskStatus.HOLDING.value]),
                    ReservationTask.last_heartbeat < stale_threshold
                )
            )
            result = await db.execute(stmt)
            stale_tasks = result.scalars().all()
            
            if not stale_tasks:
                return

            logger.info(f"ReconciliationWorker: Found {len(stale_tasks)} stale tasks for audit.")
            acc_repo = AccountRepository(db)

            for task in stale_tasks:
                await self._audit_task(db, task, acc_repo)

    async def _audit_task(self, db, task: ReservationTask, acc_repo):
        """
        Performs a deep audit of a single stale task.
        """
        logger.info(f"ReconciliationWorker: Auditing Zombie Task ID {task.id} (Status: {task.status})")
        
        account = await acc_repo.get(task.account_id)
        if not account:
            logger.error(f"ReconciliationWorker: Account {task.account_id} not found for task {task.id}")
            return

        client = WebookApiClient(
            bearer_token=account.bearer_token, 
            proxy=account.proxy_url,
            account_id=str(account.id)
        )

        try:
            # 1. Verify if account has ANY active hold for this event
            # We hit the 'my reservations' or similar endpoint to check
            # For Webook, we check the event detail which usually returns the active hold if exists.
            event_data = await client.get_event_details(task.event_slug)
            
            # Logic: If the API response contains a 'reservation' object or 'hold_token', 
            # and it matches what we might have, we reconcile to RESERVED.
            # Here we look for signs of a successful but untracked hold.
            active_reservation = event_data.get("data", {}).get("reservation")
            
            if active_reservation:
                res_id = active_reservation.get("id")
                logger.warning(f"ReconciliationWorker: RECOVERED ZOMBIE HOLD for Task {task.id} -> Reservation {res_id}")
                
                task.status = TaskStatus.RESERVED.value
                task.reservation_id = str(res_id)
                task.hold_token = active_reservation.get("hold_token")
                logs = list(task.execution_logs or [])
                logs.append({
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "msg": f"RECOVERED by Reconciler. Found Reservation {res_id}."
                })
                task.execution_logs = logs
            else:
                # No hold found, task just died mid-search. Reset to QUEUED or mark FAILED.
                logger.info(f"ReconciliationWorker: Task {task.id} verified as DEAD. Resetting to QUEUED.")
                task.status = TaskStatus.QUEUED.value
                task.worker_id = None # Release ownership
                logs = list(task.execution_logs or [])
                logs.append({
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "msg": "RECOVERED by Reconciler. Task was stale/crashed. Reset to QUEUED."
                })
                task.execution_logs = logs

            await db.commit()
            
        except Exception as e:
            logger.error(f"ReconciliationWorker: Failed to audit task {task.id}: {e}")
            await db.rollback()

