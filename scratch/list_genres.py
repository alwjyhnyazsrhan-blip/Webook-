import asyncio
from core.database.postgres import AsyncSessionLocal
from database.models.discovery import Genre
from sqlalchemy import select

async def run():
    async with AsyncSessionLocal() as db:
        genres = (await db.execute(select(Genre))).scalars().all()
        print(f"TOTAL GENRES IN DB: {len(genres)}")
        for g in genres:
            print(f" - {g.name_ar} ({g.slug})")

if __name__ == "__main__":
    asyncio.run(run())

