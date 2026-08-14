import asyncio
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database.postgres import AsyncSessionLocal
from database.models.discovery import LiveEvent
from services.discovery.taxonomy import TaxonomyEngine
from sqlalchemy import select, func

async def diagnose_taxonomy():
    print("Connecting to DB...", file=sys.stderr)
    try:
        async with AsyncSessionLocal() as db:
            count_stmt = select(func.count(LiveEvent.id))
            total = (await db.execute(count_stmt)).scalar()
            print(f"Total events in DB: {total}", file=sys.stderr)

            stmt = select(LiveEvent).where(LiveEvent.genre_id == None)
            uncategorized = (await db.execute(stmt)).scalars().all()
            
            print(f"--- Diagnosing {len(uncategorized)} Uncategorized Events ---", file=sys.stdout)
            if not uncategorized:
                print("No uncategorized events found.")
                return

            for ev in uncategorized:
                genre_id = await TaxonomyEngine.resolve_genre_id(db, ev.slug, title=ev.title_ar or ev.title_en)
                print(f"Slug: {ev.slug:40} | Title: {ev.title_ar[:30]:30} | Resolved: {genre_id}")
                if genre_id:
                    ev.genre_id = genre_id
            
            await db.commit()
            print("Finished check.", file=sys.stderr)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)

if __name__ == "__main__":
    asyncio.run(diagnose_taxonomy())
