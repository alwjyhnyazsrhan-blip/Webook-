import asyncio
import fakeredis.aioredis
from core.container import Container
from services.reservation.orchestrator import ReservationOrchestrator
from modules.ueue.worker import TaskWorker
from database.models.reservation import TaskStatus
from core.logging.logger import setup_logging, logger
from unittest.mock import patch

async def mock_handler(task_id: int):
    """Simulates a real task execution."""
    logger.info(f"Handler: Executing task {task_id}...")
    async with Container.get_db() as db:
        from database.repositories.reservation import ReservationRepository
        repo = ReservationRepository(db)
        task = await repo.get(task_id)
        if task:
            task.status = TaskStatus.SUCCESS
            await db.commit()
    logger.info(f"Handler: Task {task_id} marked as SUCCESS.")

async def verify_orchestrator_and_worker():
    setup_logging()
    logger.info("Verifying Phase 2 - Step 3: Orchestrator and Worker Runtime...")

    # Mock Redis with fakeredis
    fake_server = fakeredis.FakeServer()
    fake_redis = fakeredis.aioredis.FakeRedis(server=fake_server)
    
    with patch('core.database.redis.redis_client.client', fake_redis):
        # 1. Orchestrate Task
        async with Container.get_db() as db:
            orchestrator = ReservationOrchestrator(db)
            task = await orchestrator.start_reservation(
                user_id=888,
                event_slug="worker-test-event",
                seat_count=1
            )
        
        # Verify it's in Redis
        ueue_len = await fake_redis.llen("reservation_tasks")
        assert ueue_len == 1
        logger.info("Task successfully ueued in Redis.")

        # 2. Run Worker briefly
        worker = TaskWorker(ueue_name="reservation_tasks", concurrency_limit=2)
        
        # Start worker and stop after one cycle
        worker_task = asyncio.create_task(worker.start(mock_handler))
        
        await asyncio.sleep(2) # Wait for processing
        worker.stop()
        await asyncio.sleep(1) # Wait for loop to finish
        
        # 3. Verify Final State in DB
        async with Container.get_db() as db:
            orchestrator = ReservationOrchestrator(db)
            final_task = await orchestrator.get_task_status(task.id)
            logger.info(f"Final Task Status in DB: {final_task.status}")
            assert final_task.status == TaskStatus.SUCCESS
        
        logger.info("Orchestrator and Worker Runtime Verification SUCCESS.")

if __name__ == "__main__":
    asyncio.run(verify_orchestrator_and_worker())
