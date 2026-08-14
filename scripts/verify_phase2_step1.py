import asyncio
from core.container import Container
from database.repositories.reservation import ReservationRepository
from core.logging.logger import setup_logging, logger

async def verify_di_and_repo():
    setup_logging()
    logger.info("Verifying Phase 2 - Step 1: DI and Repository Layer...")

    # Get DB session from container
    async for db in Container.get_db():
        # Inject DB session into Repository
        repo = ReservationRepository(db)
        
        # 1. Test Create
        logger.info("Testing repository create...")
        task = await repo.create(
            user_id=999,
            event_slug="di-test-event",
            seat_count=2
        )
        logger.info(f"Task created with ID: {task.id}")
        
        # 2. Test Get
        logger.info("Testing repository get...")
        fetched_task = await repo.get(task.id)
        assert fetched_task.event_slug == "di-test-event"
        logger.info("Repository get verified.")
        
        # 3. Test Specialized Query
        logger.info("Testing domain-specific uery...")
        active_tasks = await repo.get_active_tasks()
        logger.info(f"Active tasks found: {len(active_tasks)}")
        
        logger.info("DI and Repository Layer Verification SUCCESS.")

if __name__ == "__main__":
    asyncio.run(verify_di_and_repo())
