import asyncio
from core.database.postgres import engine
from database.models import Base
from services.discovery.engine import DiscoveryEngine

async def setup():
    async with engine.begin() as conn:
        # Drop all tables to ensure new schema is applied
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("Database schema dropped and recreated.")
    await DiscoveryEngine().sync_all()
    print("Sync completed.")

if __name__ == "__main__":
    asyncio.run(setup())
