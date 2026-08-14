import asyncio
from core.database.postgres import engine
from database.models import Base

async def reset_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("Database Reset Successful")

if __name__ == "__main__":
    asyncio.run(reset_db())
