import asyncio
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database.postgres import AsyncSessionLocal
from database.models.discovery import Genre
from sqlalchemy import select

async def list_genres():
    async with AsyncSessionLocal() as db:
        stmt = select(Genre)
        genres = (await db.execute(stmt)).scalars().all()
        print(f"--- {len(genres)} Genres ---")
        for g in genres:
            print(f"Slug: {g.slug:40} | Active: {g.is_active}")

if __name__ == "__main__":
    asyncio.run(list_genres())
