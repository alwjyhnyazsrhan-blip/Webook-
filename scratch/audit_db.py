import asyncio
from core.database.postgres import AsyncSessionLocal
from database.models.discovery import Genre, LiveEvent
from sqlalchemy import select, func

async def audit():
    async with AsyncSessionLocal() as db:
        # Total events
        total_events = (await db.execute(select(func.count(LiveEvent.id)))).scalar()
        print(f"TOTAL_DB_EVENTS={total_events}")
        
        # Events per Genre
        stmt = select(Genre.slug, func.count(LiveEvent.id)).join(LiveEvent).group_by(Genre.slug)
        res = await db.execute(stmt)
        for slug, count in res.all():
            print(f"GENRE_{slug}={count}")
            
        # Hydration stats
        stmt = select(LiveEvent.hydration_status, func.count(LiveEvent.id)).group_by(LiveEvent.hydration_status)
        res = await db.execute(stmt)
        for status, count in res.all():
            print(f"STATUS_{status}={count}")

if __name__ == "__main__":
    asyncio.run(audit())

