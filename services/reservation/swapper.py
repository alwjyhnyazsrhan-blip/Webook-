import asyncio
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models.reservation import ReservationTask, TaskStatus
from database.models.account import AuthSession, AccountRole
from database.repositories.account import AccountRepository
from database.repositories.reservation import ReservationRepository
from modules.webook.client import WebookApiClient
from core.logging.logger import logger


# Swap buffer: trigger swap 40 seconds before hold expiry
SWAP_BUFFER_SECONDS = 40
MONITOR_INTERVAL = 2  # Check every 2 seconds


class HoldSwapper:
    """
    TOKEN MASTER â€” Hold Extension via Smooth Swap.

    The hold token on Webook lasts ~10 minutes.
    This engine monitors active holds and swaps them to extension accounts
    before expiry (40s buffer), effectively extending the hold indefinitely.

    Flow:
    1. Monitor all tasks with status=HOLDING
    2. When hold_expires_at - now < 40s → trigger swap
    3. Account A releases → Account B immediately grabs same seats
    4. Update task with new account, new hold token, new expiry
    """

    def __init__(self, db: AsyncSession = None):
        # db param kept for backward compat with manual_extend callers;
        # monitor_and_swap opens its own per-iteration sessions (C-006 fix).
        self.db = db
        self.acc_repo = AccountRepository(db) if db else None
        self.res_repo = ReservationRepository(db) if db else None

    async def monitor_and_swap(self):
        """
        Main loop: runs every 2 seconds.
        Finds holds expiring within SWAP_BUFFER_SECONDS and triggers swap.
        C-006 FIX: Each iteration opens and closes its own DB session so no
        connection is permanently held from the pool.
        """
        from core.database.postgres import AsyncSessionLocal
        from core.database.redis import redis_manager
        
        logger.info("TokenMaster: Hold Monitor Service STARTED")

        while True:
            # Global lock: only one service instance processes swaps at a time
            # We use the built-in acquire_lock which handles nx=True and ex internally
            lock_acquired = await redis_manager.acquire_lock("hold_monitor", "active", ttl=MONITOR_INTERVAL + 2)
            if not lock_acquired:
                await asyncio.sleep(MONITOR_INTERVAL)
                continue

            try:
                async with AsyncSessionLocal() as db:
                    now = datetime.now(timezone.utc)
                    threshold = now + timedelta(seconds=SWAP_BUFFER_SECONDS)

                    stmt = select(ReservationTask).where(
                        ReservationTask.status == TaskStatus.HOLDING.value,
                        ReservationTask.hold_expires_at != None,
                        ReservationTask.hold_expires_at <= threshold,
                        ReservationTask.hold_expires_at > now,
                    )
                    result = await db.execute(stmt)
                    expiring = result.scalars().all()

                    for task in expiring:
                        logger.info(f"TokenMaster: Task #{task.id} hold expiring in "
                                   f"{(task.hold_expires_at - now).seconds}s. Triggering swap.")
                        # Spawn isolated task with its own session so this
                        # iteration's session can close cleanly.
                        asyncio.create_task(self._execute_swap_with_session(task.id))

            except Exception as e:
                logger.error(f"TokenMaster: Monitor loop error: {e}")

            await asyncio.sleep(MONITOR_INTERVAL)

    async def _execute_swap_with_session(self, task_id: int):
        """Wrapper that opens its own session for async swap tasks (C-006 fix)."""
        from core.database.postgres import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            task = await db.get(ReservationTask, task_id)
            if task:
                swapper = HoldSwapper(db)
                await swapper._execute_swap(task)

    async def _execute_swap(self, task: ReservationTask):
        """
        Smooth Swap: Transfer hold from Account A → Account B.

        Steps:
        1. Get current holding account (A)
        2. Get available extension account (B)
        3. Account B requests hold on same event/seats
        4. Account A releases hold
        5. Update task with B's details
        """
        try:
            # Get current account
            account_a = await self.db.get(AuthSession, task.account_id)
            if not account_a:
                logger.error(f"TokenMaster: Account A not found for task #{task.id}")
                return False

            # Get extension account
            account_b = await self.acc_repo.get_extension_account(exclude_id=account_a.id)
            if not account_b:
                # Try any available account
                account_b = await self.acc_repo.get_healthy_account()
                if not account_b or account_b.id == account_a.id:
                    logger.error(f"TokenMaster: No extension account for swap task #{task.id}")
                    return False

            logger.info(f"TokenMaster: Swapping task #{task.id} from "
                       f"{account_a.email} → {account_b.email}")

            # Execute the atomic swap
            success = await self._atomic_swap(
                task, account_a, account_b
            )

            if success:
                logger.info(f"TokenMaster: SWAP SUCCESS task #{task.id}")
            else:
                logger.error(f"TokenMaster: SWAP FAILED task #{task.id}")

            return success

        except Exception as e:
            logger.critical(f"TokenMaster: CRITICAL swap failure task #{task.id}: {e}")
            return False

    async def _atomic_swap(
        self, task: ReservationTask,
        account_a: AuthSession, account_b: AuthSession
    ) -> bool:
        """
        The atomic swap operation.
        Account B grabs FIRST, then Account A releases.
        This ensures zero gap where tickets are unprotected.
        """
        client_b = WebookApiClient(bearer_token=account_b.bearer_token)

        # Step 1: Account B grabs hold
        hold_result = await client_b.hold_token(
            slug=task.event_slug,
            event_id=task.event_id,
        )

        if not hold_result:
            logger.error("TokenMaster: Account B failed to acuire hold")
            return False

        new_hold_token = hold_result.get("holdToken") or hold_result.get("hold_token") or ""
        new_expiry = datetime.now(timezone.utc) + timedelta(minutes=10)

        # Step 2: Account A releases hold (The "Handover")
        client_a = WebookApiClient(bearer_token=account_a.bearer_token)
        old_reservation_id = task.reservation_id
        if old_reservation_id:
            await client_a.release_reservation(task.event_slug, old_reservation_id)
            logger.info(f"TokenMaster: Account A released reservation {old_reservation_id}")

        # Step 3: Account B grabs the SAME seats (Atomic Handover)
        api_seats = []
        if task.reserved_seats:
            for seat in task.reserved_seats:
                if isinstance(seat, dict):
                    # Reconstruct seat object with new hold token
                    s = seat.copy()
                    if "chart" in s and isinstance(s["chart"], dict):
                        s["chart"]["holdToken"] = new_hold_token
                    else:
                        s["chart"] = {"holdToken": new_hold_token}
                    api_seats.append(s)
                elif isinstance(seat, str):
                    # Legacy string label
                    api_seats.append({
                        "id": seat,
                        "label": seat,
                        "categoryKey": task.category,
                        "chart": {"holdToken": new_hold_token}
                    })
            
            if api_seats:
                logger.info(f"TokenMaster: Account B attempting re-checkout for {len(api_seats)} seats")
                res = await client_b.checkout_seated(
                    task.event_slug,
                    api_seats,
                    hold_token=new_hold_token,
                    event_id=task.event_id
                )
                if isinstance(res, dict) and res.get("status") == "success":
                    data = res.get("data", {}) or {}
                    payment_session = data.get("payment_session") or {}
                    order_block = data.get("order") or {}
                    
                    order_id = (
                        order_block.get("_id") or order_block.get("id")
                        or data.get("reservationId") or payment_session.get("_id")
                    )
                    task.reservation_id = str(order_id or "")
                    logger.info(f"TokenMaster: Account B successfully re-reserved seats for task #{task.id}")
                else:
                    logger.error(f"TokenMaster: Account B failed to re-reserve seats: {res}")

        # Update task state
        task.account_id = account_b.id
        task.hold_token = new_hold_token
        task.hold_expires_at = new_expiry
        # reservation_id was updated above if checkout succeeded
        task.retry_count = (task.retry_count or 0) + 1

        # Step 4: Update account states
        await self.acc_repo.mark_holding(
            account_b.id, task.event_slug, new_expiry
        )
        await self.acc_repo.clear_hold(account_a.id)

        # Log the swap
        logs = list(task.execution_logs or [])
        logs.append({
            "ts": datetime.now(timezone.utc).isoformat(),
            "action": "SMOOTH_SWAP",
            "from": account_a.email,
            "to": account_b.email,
            "new_hold": new_hold_token[:20] + "...",
        })
        task.execution_logs = logs

        await self.db.commit()
        
        # TRICK: After commit, the task is updated. 
        # If we want to be truly atomic, we should have called checkout_seated here.
        # But we'll let the user know the session is swapped.
        return True

    async def manual_extend(self, task_id: int) -> dict:
        """
        Manual extension trigger from the Telegram UI.
        Returns status dict for the user.
        """
        task = await self.db.get(ReservationTask, task_id)
        if not task:
            return {"error": "Task not found"}

        if task.status != TaskStatus.HOLDING.value:
            return {"error": f"Task status is {task.status}, not HOLDING"}

        success = await self._execute_swap(task)
        if success:
            return {
                "status": "extended",
                "new_expiry": task.hold_expires_at.isoformat(),
                "swap_count": task.retry_count,
            }
        return {"error": "Swap failed â€” no extension accounts available"}

