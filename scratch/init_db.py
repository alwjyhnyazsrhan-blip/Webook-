import asyncio
from database.models.base import Base
import database.models.account
import database.models.discovery
import database.models.reservation
import database.models.user_prefs
import database.models.proxy
from core.database.postgres import engine

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created successfully.")

if __name__ == "__main__":
    asyncio.run(init_db())
