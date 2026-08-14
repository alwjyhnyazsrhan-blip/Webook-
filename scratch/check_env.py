
import asyncio
from core.config.settings import settings
from core.database.postgres import engine
from database.models import Base
from redis.asyncio import Redis

async def check():
    print("Checking database...")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("Database OK")
    except Exception as e:
        print(f"Database Failed: {e}")

    print(f"Checking Redis at {settings.redis_url}...")
    try:
        r = Redis.from_url(settings.redis_url)
        await r.ping()
        print("Redis OK")
    except Exception as e:
        print(f"Redis Failed: {e}")

if __name__ == "__main__":
    asyncio.run(check())
