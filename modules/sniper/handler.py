import asyncio
from core.database.postgres import AsyncSessionLocal
from core.database.redis import redis_manager
from database.repositories.reservation import ReservationRepository
from database.repositories.account import AccountRepository
from database.models.reservation import TaskStatus
from modules.sniper.engine import SniperEngine
from core.logging.logger import logger
from datetime import datetime, timedelta, timezone

async def execute_sniper_task(task_id: int):
    """
    Nuclear Sniper Handler: Supports Burst Mode (Multi-Account Multi-Session).
    """
    async with AsyncSessionLocal() as db:
        task_repo = ReservationRepository(db)
        account_repo = AccountRepository(db)
        
        task = await task_repo.get(task_id)
        if not task: return

        # 1. Burst Mode: Acquire multiple accounts for this task to increase win rate
        # We try to grab up to 3 accounts for a high-priority 'Nuclear' attack
        accounts = await account_repo.get_available_accounts()
        target_sessions = []
        
        for acc in accounts:
            if await redis_manager.acquire_lock(f"account:{acc.id}", owner_id="handler", ttl=60):
                target_sessions.append(acc)
                if len(target_sessions) >= 3: break # Cap burst at 3 accounts
        
        if not target_sessions:
            logger.warning(f"No accounts available for task {task_id}. Back to queue.")
            await redis_manager.enqueue_task(task_id)
            return

        # 2. Parallel Attack: Launch engines for each account simultaneously
        engines = [SniperEngine(acc) for acc in target_sessions]
        
        try:
            task.status = TaskStatus.RUNNING.value
            await db.commit()

            # The Nuclear Launch
            results = await asyncio.gather(*[
                eng.execute_reservation(task.event_slug, task.seat_count, task.category, task.zone)
                for eng in engines
            ], return_exceptions=True)

            # 3. Handle First Success (The Winner)
            for res in results:
                if isinstance(res, dict) and "id" in res:
                    task.status = TaskStatus.SUCCESS.value
                    task.hold_token = res.get("id")
                    task.hold_expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
                    task.logs.append({"t": str(datetime.now(timezone.utc)), "msg": f"WINNER: Hold obtained by {res.get('account_email')}"})
                    await db.commit()
                    logger.info(f"Task {task_id} WON by one of the burst engines!")
                    break
        finally:
            # Release all locks
            for acc in target_sessions:
                await redis_manager.release_lock(f"account:{acc.id}")
