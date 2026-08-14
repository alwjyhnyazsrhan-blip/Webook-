
import asyncio
import sys
import os

# Add project root to sys.path
sys.path.append(os.getcwd())

from core.database.postgres import engine
from database.models.discovery import Base
from database.models.reservation import Base as ResBase
from database.models.account import Base as AccBase

async def init_db():
    print("--- INITIALIZING DATABASE ---")
    async with engine.begin() as conn:
        # Import all models to ensure they are registered with Base
        import database.models.discovery
        import database.models.reservation
        import database.models.account
        
        await conn.run_sync(Base.metadata.create_all)
        print("Tables created.")

if __name__ == "__main__":
    asyncio.run(init_db())
