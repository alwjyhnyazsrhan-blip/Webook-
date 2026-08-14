import asyncio
from sqlalchemy import select
from database.models.reservation import ReservationTask, TaskStatus
from database.models.discovery import LiveEvent, SeatMapCache
from database.models.account import AccountHealth
from database.repositories.account import AccountRepository
from database.repositories.reservation import ReservationRepository
from core.database.redis import redis_manager
from core.logging.logger import logger
from datetime import datetime, timezone

class ReservationOrchestrator:
    """
    The Mission Commander. 
    Validates pre-flight conditions, locks resources, and dispatches tasks to the worker.
    """
    def __init__(self, db_session):
        self.db = db_session
        self.acc_repo = AccountRepository(db_session)
        self.res_repo = ReservationRepository(db_session)

    async def start_reservation(self, user_id: int, slug: str = None, category_id: str = None, count: int = 1, timeslot_id: str = None, team_id: str = None, task_id: int = None, trace_id: str = None, root_trace_id: str = None, depth: int = 0):
        """
        PHASE 7: REAL EXECUTION ENGINE
        Wires the UI request to the real distributed execution logic.
        """
        logger.info(f"[ORCHESTRATOR_START] user_id={user_id} slug={slug} task_id={task_id}")
        try:
            count = max(1, min(int(count), 5))
        except Exception:
            count = 1

        # Validate: must have slug if no task_id
        if not task_id and not slug:
            raise ValueError("\u0645\u0639\u0631\u0641 \u0627\u0644\u0641\u0639\u0627\u0644\u064a\u0629 \u0645\u0637\u0644\u0648\u0628.")

        # 1. Fetch or Create Task
        if task_id:
            task = await self.db.get(ReservationTask, task_id)
            if not task: 
                logger.error(f"[ORCHESTRATOR_ERROR] Task {task_id} not found.")
                raise ValueError("\u0627\u0644\u0645\u0647\u0645\u0629 \u063a\u064a\u0631 \u0645\u0648\u062c\u0648\u062f\u0629.")
            slug = task.event_slug
            if trace_id:
                task.trace_id = trace_id
        else:
            # Legacy/Manual create (keep for compatibility)
            account = await self.acc_repo.get_sniper_account()
            if not account: 
                logger.warning("[ORCHESTRATOR_FAILED] No verified accounts available.")
                raise ValueError("\u0644\u0627 \u062a\u0648\u062c\u062f \u062d\u0633\u0627\u0628\u0627\u062a \u0645\u0648\u062b\u0642\u0629.")
            selection_context = {
                "ticket_id": str(category_id) if category_id is not None else None,
                "ticket_title": None,
                "ticket_slug": None,
                "category_key": None,
                "category_label": str(category_id) if category_id is not None else None,
                "timeslot_id": timeslot_id,
                "team_id": team_id,
                "source": "legacy_orchestrator",
            }
            task = ReservationTask(
                user_id=user_id,
                account_id=account.id,
                event_slug=slug,
                category=selection_context.get("category_label"),
                timeslot_id=timeslot_id,
                team_id=team_id,
                seat_count=count,
                status=TaskStatus.CREATED.value,
                trace_id=trace_id,
                root_trace_id=root_trace_id,
                depth=depth,
                execution_logs=[{
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "msg": "SELECTION_CONTEXT",
                    "selection_context": selection_context,
                }],
                created_at=datetime.now(timezone.utc)
            )
            self.db.add(task)
            await self.db.flush()
            logger.info(f"[ORCHESTRATOR_CREATED] task_id={task.id} account_id={account.id} trace_id={trace_id}")

        # 2. Account Binding (if not already bound or if bound account is unhealthy)
        if not task.account_id:
            account = await self.acc_repo.get_sniper_account()
            if not account: 
                logger.warning(f"[ORCHESTRATOR_FAILED] Task {task.id} - No verified accounts available.")
                raise ValueError("\u0644\u0627 \u062a\u0648\u062c\u062f \u062d\u0633\u0627\u0628\u0627\u062a \u0645\u0648\u062b\u0642\u0629.")
            task.account_id = account.id
        else:
            account = await self.acc_repo.get(task.account_id)
            if not account or account.health != AccountHealth.ACTIVE.value:
                # Re-bind to a healthy sniper if the bound one died
                logger.info(f"[ORCHESTRATOR_REBIND] Task {task.id} account {task.account_id} unhealthy. Searching for replacement...")
                new_account = await self.acc_repo.get_sniper_account()
                if not new_account:
                    raise ValueError("\u0627\u0644\u062d\u0633\u0627\u0628 \u0627\u0644\u0645\u0631\u062a\u0628\u0637 \u063a\u064a\u0631 \u0645\u062a\u0627\u062d \u062d\u0627\u0644\u064a\u0627 \u0648\u0644\u0627 \u064a\u0648\u062c\u062f \u0628\u062f\u064a\u0644.")
                task.account_id = new_account.id
                account = new_account

        # 5. Dispatch to Execution Queue
        task.status = TaskStatus.QUEUED.value
        await self.db.commit()
        logger.info(f"[ORCHESTRATOR_QUEUED] task_id={task.id} status={task.status}")
        
        # Real-time push to Redis queue
        try:
            await redis_manager.enqueue_task(task.id)
            logger.info(f"[ORCHESTRATOR_DISPATCHED] task_id={task.id} engine=redis_worker")
        except Exception as e:
            logger.warning(f"[ORCHESTRATOR_DISPATCH_FALLBACK] task_id={task.id} error={e}")
        
        return task

    async def start_mass_snipe(self, user_id: int, slug: str, category_id: str = None, count: int = 1, timeslot_id: str = None, team_id: str = None, trace_id: str = None) -> list:
        """
        MASS-SNIPE: Fan out to ALL healthy accounts simultaneously via asyncio.gather.
        Creates one task per account, all queued at T=0 with sniper_mode=True (no human delays).
        Returns list of created tasks.
        """
        logger.info(f"[MASS_SNIPE_START] user_id={user_id} slug={slug} category={category_id} count={count}")
        try:
            count = max(1, min(int(count), 5))
        except Exception:
            count = 1

        # Fetch all healthy accounts
        accounts = await self.acc_repo.get_available_accounts()
        active_accounts = [a for a in accounts if a.health == "ACTIVE" and a.bearer_token]

        if not active_accounts:
            logger.warning("[MASS_SNIPE_FAILED] No active accounts with bearer tokens")
            raise ValueError("\u0644\u0627 \u062a\u0648\u062c\u062f \u062d\u0633\u0627\u0628\u0627\u062a \u0646\u0634\u0637\u0629 \u0644\u0644\u0633\u0646\u0627\u064a\u0628\u064a\u0646\u062c.")

        logger.info(f"[MASS_SNIPE_ACCOUNTS] Fanning out to {len(active_accounts)} accounts")

        # Create one task per account, all with sniper_mode=True
        tasks = []
        for account in active_accounts:
            selection_context = {
                "ticket_id": str(category_id) if category_id is not None else None,
                "ticket_title": None,
                "ticket_slug": None,
                "category_key": None,
                "category_label": str(category_id) if category_id is not None else None,
                "timeslot_id": timeslot_id,
                "team_id": team_id,
                "source": "mass_snipe",
            }
            task = ReservationTask(
                user_id=user_id,
                account_id=account.id,
                event_slug=slug,
                category=selection_context.get("category_label"),
                timeslot_id=timeslot_id,
                team_id=team_id,
                seat_count=count,
                status=TaskStatus.QUEUED.value,
                sniper_mode=True,
                trace_id=trace_id,
                execution_logs=[{
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "msg": "SELECTION_CONTEXT",
                    "selection_context": selection_context,
                }],
                created_at=datetime.now(timezone.utc)
            )
            self.db.add(task)
            tasks.append(task)

        await self.db.flush()  # Assign IDs
        await self.db.commit()

        # Dispatch ALL tasks to Redis simultaneously
        dispatch_results = await asyncio.gather(
            *[redis_manager.enqueue_task(t.id) for t in tasks],
            return_exceptions=True
        )

        success_count = sum(1 for r in dispatch_results if not isinstance(r, Exception))
        logger.info(f"[MASS_SNIPE_DISPATCHED] {success_count}/{len(tasks)} tasks enqueued")

        return tasks
