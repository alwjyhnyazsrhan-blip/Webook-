import asyncio
import os
from core.database.postgres import engine
from database.models.base import Base
from database.models.discovery import Genre, LiveEvent, SeatMapCache
from database.models.reservation import ReservationTask
from database.models.account import AuthSession

async def reset_db():
    print("RESETTING DATABASE...")
    async with engine.begin() as conn:
        # Drop all tables
        await conn.run_sync(Base.metadata.drop_all)
        # Create all tables with correct schema
        await conn.run_sync(Base.metadata.create_all)
    print("DATABASE RESET SUCCESSFUL")

if __name__ == "__main__":
    asyncio.run(reset_db())
