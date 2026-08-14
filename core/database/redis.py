import redis.asyncio as redis
import json
from typing import Optional
from core.config.settings import settings
from core.logging.logger import logger

class RedisManager:
    """
    Production Redis Manager.
    Strictly enforced real Redis usage. Fail-hard on connection loss to prevent distributed race conditions.
    """
    def __init__(self):
        self.client: Optional[redis.Redis] = None
        self._url = settings.redis_url

    async def connect(self):
        try:
            self.client = redis.from_url(
                self._url, 
                encoding="utf-8", 
                decode_responses=True,
                socket_timeout=5.0,
                socket_connect_timeout=2.0,
                retry_on_timeout=False
            )
            # Verify connection immediately
            await self.client.ping()
            logger.info(f"RedisManager: Connected to persistent storage at {self._url}")
        except Exception as e:
            logger.warning(f"RedisManager: Real Redis unavailable ({e}). Falling back to FAKEREDIS for local run.")
            try:
                import fakeredis.aioredis as fakeredis_async
                self.client = fakeredis_async.FakeRedis(decode_responses=True)
                logger.warning("RedisManager: FAKEREDIS ACTIVE. Note: Locks are NOT persistent across restarts.")
            except ImportError:
                logger.critical("RedisManager: FAKEREDIS not found and real Redis failed.")
                raise RuntimeError("CRITICAL: Redis is reuired. Install fakeredis or start a real Redis server.")

    async def acquire_lock(self, key: str, owner_id: str, ttl: int = 30) -> bool:
        """
        Atomic distributed lock using SET NX PX.
        Stores owner_id as value for verification.
        """
        if not self.client: await self.connect()
        return await self.client.set(f"lock:{key}", owner_id, nx=True, ex=ttl)

    async def renew_lock(self, key: str, owner_id: str, ttl: int = 30) -> bool:
        """
        Extends TTL ONLY if owner_id matches.
        """
        if not self.client: await self.connect()
        # Atomic Lua script for safe renewal
        script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("expire", KEYS[1], ARGV[2])
        else
            return 0
        end
        """
        result = await self.client.eval(script, 1, f"lock:{key}", owner_id, ttl)
        return bool(result)

    async def release_lock(self, key: str):
        if self.client:
            await self.client.delete(f"lock:{key}")

    async def enqueue_task(self, task_id: int):
        if not self.client: await self.connect()
        await self.client.lpush("reservation_queue", str(task_id))

    async def dequeue_task(self) -> Optional[str]:
        if not self.client: await self.connect()
        # Keep the Redis socket timeout above this blocking wait so an idle queue
        # returns None instead of logging a network timeout.
        res = await self.client.brpop("reservation_queue", timeout=1)
        return res[1] if res else None

    async def get(self, key: str) -> Optional[str]:
        if not self.client: await self.connect()
        return await self.client.get(key)

    async def set(self, key: str, value: str, ex: Optional[int] = None, **kwargs):
        if not self.client: await self.connect()
        logger.debug(f"RedisManager: SET {key} (ex={ex})")
        return await self.client.set(key, value, ex=ex, **kwargs)

    async def delete(self, key: str):
        if not self.client: await self.connect()
        await self.client.delete(key)

    async def close(self):
        if not self.client:
            return
        closer = getattr(self.client, "aclose", None) or getattr(self.client, "close", None)
        if closer:
            result = closer()
            if hasattr(result, "__await__"):
                await result
        self.client = None
        logger.info("RedisManager: Connection closed")

redis_manager = RedisManager()
