import asyncio
import random
import logging
from unittest.mock import patch
from sqlalchemy.exc import IntegrityError, OperationalError
from httpx import ReadTimeout, ConnectTimeout

logger = logging.getLogger("ChaosInjector")
logger.setLevel(logging.INFO)

import os

class ChaosConfig:
    SEED = int(os.environ.get("CHAOS_SEED", 42))  # Deterministic replayability
    random.seed(SEED)
    logger.info(f"[CHAOS_SEED] Initialized chaos engine with deterministic seed: {SEED}")

    DB_COMMIT_FAILURE_RATE = 0.05       # 5% chance DB commit fails
    CHECKOUT_TIMEOUT_RATE = 0.10        # 10% chance Webook checkout timeouts
    REDIS_LATENCY_MAX_MS = 200          # Add up to 200ms latency to redis dequeues
    DUPLICATE_DELIVERY_RATE = 0.05      # 5% chance same queue task is returned twice

def inject_chaos():
    """
    Monkey-patches core infrastructure (DB, HTTP, Redis) to simulate 
    distributed failures, network partitions, and split-brain scenarios.
    """
    logger.warning("🌪️ CHAOS INJECTOR ACTIVATED: The system is now operating under hostile conditions.")
    
    # 1. DB Commit Failures
    from database.core import AsyncSessionLocal
    original_commit = getattr(AsyncSessionLocal, 'commit', None)
    
    if hasattr(AsyncSessionLocal, 'commit'):
        # Because AsyncSessionLocal is usually a factory returning an AsyncSession, 
        # we need to patch the actual AsyncSession.commit
        from sqlalchemy.ext.asyncio import AsyncSession
        original_async_commit = AsyncSession.commit
        
        async def chaos_commit(self, *args, **kwargs):
            if random.random() < ChaosConfig.DB_COMMIT_FAILURE_RATE:
                logger.error("[CHAOS] 💥 Simulated Database Commit Failure (OperationalError)")
                raise OperationalError("Simulated DB connection drop during commit", params=None, orig=None)
            return await original_async_commit(self, *args, **kwargs)
            
        AsyncSession.commit = chaos_commit
        logger.info("[CHAOS_HOOK] Database commits weaponized (5% failure rate).")

    # 2. Checkout Timeouts
    from modules.webook.client import WebookApiClient
    original_checkout = WebookApiClient.checkout_seated
    
    async def chaos_checkout_seated(self, *args, **kwargs):
        if random.random() < ChaosConfig.CHECKOUT_TIMEOUT_RATE:
            logger.error("[CHAOS] ⏱️ Simulated Webook API Timeout (ReadTimeout)")
            raise ReadTimeout("Simulated API timeout during checkout")
        return await original_checkout(self, *args, **kwargs)
        
    WebookApiClient.checkout_seated = chaos_checkout_seated
    logger.info("[CHAOS_HOOK] Webook API checkout weaponized (10% timeout rate).")
    
    # 3 & 4. Redis Latency & Duplicate Delivery
    try:
        from core.network.redis_manager import RedisManager
        original_dequeue = RedisManager.dequeue_task
        
        async def chaos_dequeue(self, *args, **kwargs):
            # Inject Latency
            latency = random.uniform(0, ChaosConfig.REDIS_LATENCY_MAX_MS) / 1000.0
            await asyncio.sleep(latency)
            
            task_id = await original_dequeue(self, *args, **kwargs)
            
            # Duplicate Delivery Simulation
            if task_id and random.random() < ChaosConfig.DUPLICATE_DELIVERY_RATE:
                logger.error(f"[CHAOS] 👯 Simulated Split-Brain: Re-queueing task_id={task_id} while it's being returned!")
                await self.enqueue_task(task_id) # Put it back so another worker grabs it instantly
                
            return task_id
            
        RedisManager.dequeue_task = chaos_dequeue
        logger.info("[CHAOS_HOOK] Redis queue weaponized (Latency + 5% Duplicate Delivery rate).")
    except ImportError:
        pass

if __name__ == "__main__":
    inject_chaos()
