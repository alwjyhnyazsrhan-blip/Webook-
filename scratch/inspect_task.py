import asyncio
from core.database.postgres import AsyncSessionLocal
from database.models.reservation import ReservationTask
from database.models.discovery import LiveEvent

async def main():
    async with AsyncSessionLocal() as db:
        task = await db.get(ReservationTask, 6)
        print("Task 6 details:")
        print(f"  id: {task.id}")
        print(f"  event_slug: {task.event_slug}")
        print(f"  category: {task.category}")
        print(f"  seat_count: {task.seat_count}")
        print(f"  status: {task.status}")
        
        # Fetch event
        from sqlalchemy import select
        evt = (await db.execute(select(LiveEvent).where(LiveEvent.slug == task.event_slug))).scalar_one_or_none()
        if evt:
            print("\nLiveEvent details:")
            print(f"  id: {evt.id}")
            print(f"  event_key: {evt.event_key}")
            print(f"  workspace_key: {evt.workspace_key}")
            print(f"  chart_key: {evt.chart_key}")
            
            # Print tickets from metadata_json
            meta = evt.metadata_json or {}
            print(f"\nMetadata keys: {list(meta.keys())}")
            tickets = meta.get("tickets", []) or meta.get("data", {}).get("tickets", [])
            print(f"\nTickets count: {len(tickets)}")
            for t in tickets:
                print(f"  Ticket: id={t.get('id') or t.get('_id')} title_ar={t.get('title_ar') or t.get('title')} price={t.get('price')} is_sold_out={t.get('is_sold_out')} category_key={t.get('category_key')} seats_io_category={t.get('seats_io_category')}")
        else:
            print("Event not found in DB!")

asyncio.run(main())
