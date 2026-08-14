import asyncio
from services.discovery.engine import DiscoveryEngine
from core.database.postgres import AsyncSessionLocal
from database.models.discovery import LiveEvent
from sqlalchemy import select, func

async def test_sync_depth():
    engine = DiscoveryEngine()
    print("STARTING TEST SYNC (Page 0)...")
    async with AsyncSessionLocal() as db:
        # Check count before
        count_before = (await db.execute(select(func.count(LiveEvent.id)))).scalar()
        print(f"COUNT BEFORE: {count_before}")
        
        # Run sync for one page
        res = await engine.api.get_all_upcoming_events(per_page=50, page=0)
        events = res.get("events", [])
        print(f"API RETURNED {len(events)} EVENTS")
        
        for ev in events:
            await engine._upsert_event_shell(db, ev)
        
        await db.commit()
        
        # Check count after
        count_after = (await db.execute(select(func.count(LiveEvent.id)))).scalar()
        print(f"COUNT AFTER: {count_after}")
        
        if count_after == count_before:
            print("WARNING: No new events saved! Checking first event details...")
            if events:
                print(f"FIRST EVENT API: ID={events[0].get('_id')} | SLUG={events[0].get('slug')}")
                # Check if it exists in DB
                stmt = select(LiveEvent).where(LiveEvent.slug == events[0].get('slug'))
                db_ev = (await db.execute(stmt)).scalar_one_or_none()
                if db_ev:
                    print(f"FOUND IN DB: ID={db_ev.webook_id} | SLUG={db_ev.slug}")

if __name__ == "__main__":
    asyncio.run(test_sync_depth())

