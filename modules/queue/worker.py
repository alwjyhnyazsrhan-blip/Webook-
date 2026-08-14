import asyncio
import json
from typing import Callable, Awaitable
from core.database.redis import redis_manager
from core.database.postgres import AsyncSessionLocal
from database.repositories.reservation import ReservationRepository
from database.models.reservation import TaskStatus
from core.logging.logger import logger


class TaskWorker:
    """
    High-performance async task consumer.
    Pulls tasks from Redis and executes them using the provided handler.
    """

    def __init__(self, queue_name: str, concurrency_limit: int = 10):
        self.queue_name = queue_name            # Fix: was 'ueue_name' (missing q)
        self.concurrency_limit = concurrency_limit
        self.semaphore = asyncio.Semaphore(concurrency_limit)
        self.is_running = False

    async def start(self, handler: Callable[[int], Awaitable[None]]):
        """Starts the worker loop."""
        self.is_running = True
        logger.info(f"Worker started on queue: {self.queue_name}", concurrency=self.concurrency_limit)

        while self.is_running:
            try:
                # Blocking pop from Redis; returns task_id or None
                tid = await redis_manager.dequeue_task()
                if tid:
                    task_id = int(tid)
                    # Spawn task in background up to concurrency limit
                    asyncio.create_task(self._safe_execute(task_id, handler))

            except Exception as e:
                logger.error("Worker loop error", error=str(e))
                await asyncio.sleep(1)

    async def _safe_execute(self, task_id: int, handler: Callable[[int], Awaitable[None]]):
        """Executes handler with semaphore control and error handling."""
        async with self.semaphore:
            logger.info(f"Worker: Processing task {task_id}")
            try:
                await handler(task_id)
            except Exception as e:
                logger.error(f"Task {task_id} failed in worker", error=str(e))
                await self._mark_task_failed(task_id, str(e))

    async def _mark_task_failed(self, task_id: int, error: str):
        """Ensures task is marked failed in DB if the handler crashes."""
        async with AsyncSessionLocal() as db:
            repo = ReservationRepository(db)
            task = await repo.get(task_id)
            if task:
                # Fix 7: must write .value (string) not the enum object
                task.status = TaskStatus.FAILED.value
                task.error_message = f"Worker Error: {error}"
                await db.commit()

    def stop(self):
        self.is_running = False
        logger.info(f"Worker stopping on queue: {self.queue_name}")
