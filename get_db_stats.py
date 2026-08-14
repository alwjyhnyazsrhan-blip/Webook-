import asyncio
import sys
import os
import json

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database.postgres import AsyncSessionLocal
from database.models.discovery import LiveEvent, Genre
from sqlalchemy import select, func

async def get_db_stats():
    stats = {}
    async with AsyncSessionLocal() as db:
        # Total events
        stats["total_events"] = (await db.execute(select(func.count(LiveEvent.id)))).scalar()
        # Categorized
        stats["categorized"] = (await db.execute(select(func.count(LiveEvent.id)).where(LiveEvent.genre_id != None))).scalar()
        # Uncategorized
        stats["uncategorized"] = (await db.execute(select(func.count(LiveEvent.id)).where(LiveEvent.genre_id == None))).scalar()
        # Total genres
        stats["total_genres"] = (await db.execute(select(func.count(Genre.id)))).scalar()
        # Active genres
        stats["active_genres"] = (await db.execute(select(func.count(Genre.id)).where(Genre.is_active == True))).scalar()
        
        # Sample uncategorized slugs
        stmt = select(LiveEvent.slug).where(LiveEvent.genre_id == None).limit(10)
        stats["sample_uncategorized"] = [(await db.execute(stmt)).scalars().all()]
        
    with open("db_stats_evidence.json", "w") as f:
        json.dump(stats, f, indent=4)
    print("Stats written to db_stats_evidence.json")

if __name__ == "__main__":
    try:
        asyncio.run(get_db_stats())
    except Exception as e:
        with open("db_stats_error.txt", "w") as f:
            f.write(str(e))
        print(f"Error: {e}")
