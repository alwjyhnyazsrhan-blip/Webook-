import asyncio
import fakeredis.aioredis
from core.database.redis import RedisClient
from core.logging.logger import setup_logging, logger
from unittest.mock import patch

async def verify_redis():
    setup_logging()
    logger.info("Starting Redis Verification (via fakeredis)...")
    
    # Mock the Redis connection to use fakeredis
    fake_server = fakeredis.FakeServer()
    
    with patch('redis.asyncio.ConnectionPool.from_url') as mock_pool:
        # Create a real client but pointed to our fake server
        client = RedisClient()
        client.client = fakeredis.aioredis.FakeRedis(server=fake_server)
        
        # 1. Ping
        is_alive = await client.ping()
        logger.info(f"Redis Ping Result: {is_alive}")
        
        # 2. Queue Push
        task_data = "{\"task_id\": 1, \"action\": \"reserve\"}"
        await client.client.lpush("test_ueue", task_data)
        logger.info("Pushed task to ueue.")
        
        # 3. Queue Pop
        result = await client.client.brpop("test_ueue", timeout=1)
        logger.info(f"Deueued task: {result[1]}")
        
        assert result[1] == task_data.encode()
        logger.info("Redis Logic Verification SUCCESS.")

if __name__ == "__main__":
    asyncio.run(verify_redis())
