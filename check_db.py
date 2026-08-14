import asyncio
import os
import sys
sys.path.append(os.getcwd())

async def check():
    from core.database.postgres import AsyncSessionLocal
    from database.models.discovery import LiveEvent, Genre
    from sqlalchemy import select, func
    
    async with AsyncSessionLocal() as db:
        total = await db.scalar(select(func.count(LiveEvent.id)))
        active_genres = (await db.execute(select(Genre.slug, Genre.name_ar).where(Genre.is_active == True))).all()
        
        print(f"Total Events: {total}")
        print(f"Active Categories: {len(active_genres)}")
        for g in active_genres:
            print(f" - {g[0]}: {g[1]}")

if __name__ == '__main__':
    asyncio.run(check())
