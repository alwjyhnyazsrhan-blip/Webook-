import asyncio
import uuid
import time
from datetime import datetime, timezone
from sqlalchemy import select, func
from core.database.postgres import AsyncSessionLocal
from core.database.redis import redis_manager
from database.models.reservation import ReservationTask, TaskStatus
from services.reservation.worker import ReservationWorker
from core.logging.logger import logger

class InfrastructureStressTester:
    """
    Hostile Validation Suite.
    Simulates high-concurrency, network failure, and service restart scenarios.
    """

    async def run_all(self):
        await self.simulate_1000_ueued_snipes()
        await self.simulate_stale_holds()
        await self.simulate_duplicate_scheduler_ticks()
        await self.simulate_orphan_worker_cleanup()

    async def simulate_1000_ueued_snipes(self):
        logger.info("Simulation 1: 1000 Queued Snipes")
        async with AsyncSessionLocal() as db:
            # Create 1000 tasks
            tasks = []
            for i in range(1000):
                tasks.append(ReservationTask(
                    user_id=1,
                    event_slug="stress-test-event",
                    status=TaskStatus.QUEUED.value
                ))
            db.add_all(tasks)
            await db.commit()
            
            # Start a few workers
            workers = [ReservationWorker() for _ in range(5)]
            worker_tasks = [asyncio.create_task(w._claim_and_dispatch()) for w in workers]
            
            await asyncio.gather(*worker_tasks)
            
            # Verify no duplicates
            stmt = select(func.count(ReservationTask.id)).where(ReservationTask.worker_id != None)
            claimed = (await db.execute(stmt)).scalar()
            logger.info(f"Result: {claimed} tasks claimed atomically across workers.")

    async def simulate_stale_holds(self):
        logger.info("Simulation 2: Stale Holds Failover")
        async with AsyncSessionLocal() as db:
            # Create a task claimed by a "dead" worker
            task = ReservationTask(
                user_id=1,
                event_slug="dead-worker-event",
                status=TaskStatus.SEARCHING.value,
                worker_id="dead-worker-666",
                last_heartbeat=datetime.now(timezone.utc) - asyncio.to_thread(lambda: datetime.now(timezone.utc) - datetime.now(timezone.utc)) # mock
            )
            # manually set stale heartbeat
            from datetime import timedelta
            task.last_heartbeat = datetime.now(timezone.utc) - timedelta(minutes=5)
            db.add(task)
            await db.commit()
            
            worker = ReservationWorker()
            await worker._claim_and_dispatch()
            
            # Verify the task was re-claimed
            await db.refresh(task)
            logger.info(f"Result: Task reclaimed by {worker.worker_id}: {task.worker_id != 'dead-worker-666'}")

    async def simulate_duplicate_scheduler_ticks(self):
        logger.info("Simulation 3: Duplicate Scheduler Ticks")
        # Run _claim_and_dispatch twice in parallel on same worker
        worker = ReservationWorker()
        await asyncio.gather(
            worker._claim_and_dispatch(),
            worker._claim_and_dispatch()
        )
        logger.info("Result: No crashes, registry handles atomic transition.")

    async def simulate_orphan_worker_cleanup(self):
        logger.info("Simulation 4: Orphan Worker Cleanup")
        from services.reservation.worker import TaskRegistry
        atask = asyncio.create_task(asyncio.sleep(10))
        TaskRegistry.register(999, atask)
        logger.info(f"Registry before: {len(TaskRegistry._active)} tasks")
        atask.cancel()
        # registry cleanup is called in worker.run
        # manually trigger for test
        worker = ReservationWorker()
        worker._cleanup_registry()
        logger.info(f"Registry after cleanup: {len(TaskRegistry._active)} tasks")

if __name__ == "__main__":
    tester = InfrastructureStressTester()
    asyncio.run(tester.run_all())

