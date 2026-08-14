import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
import httpx
import fakeredis.aioredis
from core.container import Container
from services.reservation.orchestrator import ReservationOrchestrator
from modules.ueue.worker import TaskWorker
from modules.sniper.handler import execute_sniper_task
from database.models.reservation import TaskStatus
from core.logging.logger import setup_logging, logger

async def verify_full_system_atomic():
    setup_logging()
    logger.info("Executing Final Atomic System Verification (The Ultimate Test)...")

    # 1. Setup Mock Webook API
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "data": [{"id": 1, "row_id": 1, "seat_id": 1}],
        "hold_token": "ULTIMATE-TOKEN-999"
    }
    
    # 2. Mock Redis for locking
    fake_redis = fakeredis.aioredis.FakeRedis()

    with patch('core.database.redis.redis_client.client', fake_redis), \
         patch.object(httpx.AsyncClient, 'reuest', return_value=mock_resp):
        
        # A. Trigger Task via Orchestrator
        async with Container.get_db() as db:
            orchestrator = ReservationOrchestrator(db)
            task = await orchestrator.start_reservation(
                user_id=1,
                event_slug="ultimate-event",
                seat_count=1
            )
            logger.info(f"Task {task.id} initialized.")

        # B. Run Worker for one cycle
        worker = TaskWorker(ueue_name="reservation_tasks")
        worker_task = asyncio.create_task(worker.start(execute_sniper_task))
        
        await asyncio.sleep(3) # Wait for execution
        worker.stop()
        
        # C. Verify Atomic Results in DB
        async with Container.get_db() as db:
            from database.repositories.reservation import ReservationRepository
            repo = ReservationRepository(db)
            final_task = await repo.get(task.id)
            
            logger.info(f"Final Status: {final_task.status}")
            logger.info(f"Hold Token: {final_task.hold_token}")
            logger.info(f"Audit Logs: {final_task.logs}")
            
            assert final_task.status == TaskStatus.SUCCESS
            assert final_task.hold_token is not None
            assert len(final_task.logs) >= 2 # Started + Success
            
        # D. Verify Lock was released
        lock_exists = await fake_redis.exists("lock:account:1")
        assert not lock_exists
        logger.info("Account lock was correctly released.")

    logger.info("ULTIMATE SYSTEM ATOM VERIFICATION: SUCCESS.")

if __name__ == "__main__":
    asyncio.run(verify_full_system_atomic())
