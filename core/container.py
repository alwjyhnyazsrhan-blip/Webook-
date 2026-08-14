from typing import AsyncGenerator
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from core.database.postgres import AsyncSessionLocal
from core.database.redis import redis_manager
from core.logging.logger import logger

class Container:
    """
    Centralized Dependency Injection Container.
    Manages the lifecycle of infrastructure components and services.
    """
    
    @staticmethod
    @asynccontextmanager
    async def get_db() -> AsyncGenerator[AsyncSession, None]:
        """Provides a scoped database session."""
        async with AsyncSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error("Database session error", error=str(e))
                raise
            finally:
                await session.close()

    @staticmethod
    def get_redis():
        """Provides the global redis client."""
        return redis_manager.client

    # Service factories will be added here as we implement them

