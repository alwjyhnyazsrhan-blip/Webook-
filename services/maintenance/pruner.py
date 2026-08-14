import asyncio
from datetime import datetime, timedelta, timezone
from sqlalchemy import delete
from core.database.postgres import AsyncSessionLocal
from database.models.reservation import ReservationTask, TaskStatus
from core.logging.logger import logger

async def prune_old_tasks():
    """
    Background worker that prunes old successful/failed tasks to keep DB lean.
    """
    logger.info("Maintenance: Starting Pruner Service...")
    while True:
        try:
            async with AsyncSessionLocal() as db:
                # Delete successful tasks older than 24 hours
                threshold = datetime.now(timezone.utc) - timedelta(hours=24)
                
                stmt = delete(ReservationTask).where(
                    ReservationTask.status.in_([TaskStatus.SUCCESS, TaskStatus.FAILED, TaskStatus.CANCELLED]),
                    ReservationTask.updated_at <= threshold
                )
                
                result = await db.execute(stmt)
                await db.commit()
                
                if result.rowcount > 0:
                    logger.info(f"Maintenance: Pruned {result.rowcount} old tasks.")
            
            # Run every hour
            await asyncio.sleep(3600)
        except Exception as e:
            logger.error("Maintenance: Pruner loop failed", error=str(e))
            await asyncio.sleep(60)

