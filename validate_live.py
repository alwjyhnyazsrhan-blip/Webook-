import asyncio
import sys
import json

async def run_live_validation():
    print("=" * 60)
    print("LIVE WEOOK BOT VALIDATION")
    print("=" * 60)
    
    from core.database.postgres import AsyncSessionLocal
    from database.models.discovery import LiveEvent, Genre
    from database.models.account import AuthSession
    from sqlalchemy import select, func
    from services.discovery.engine import DiscoveryEngine
    from modules.webook.client import WebookApiClient
    
    # 1. Check database state
    print("\n[1] DATABASE STATE CHECK")
    print("-" * 40)
    async with AsyncSessionLocal() as db:
        total_events = await db.scalar(select(func.count(LiveEvent.id)))
        ready_events = await db.scalar(select(func.count(LiveEvent.id)).where(LiveEvent.hydration_status == "READY"))
        ghost_events = await db.scalar(select(func.count(LiveEvent.id)).where(LiveEvent.status == "GHOST"))
        genres = (await db.execute(select(func.count(Genre.id)))).scalar()
        
        print(f"Total events in DB: {total_events}")
        print(f"READY events: {ready_events}")
        print(f"GHOST events: {ghost_events}")
        print(f"Total genres: {genres}")
        
        # Get some sample events
        stmt = select(LiveEvent).where(LiveEvent.hydration_status == "READY").limit(5)
        sample_events = (await db.execute(stmt)).scalars().all()
        
        print(f"\nSample READY events:")
        for e in sample_events:
            print(f"  - {e.slug} | {e.title_ar[:40]} | {e.starts_at}")
    
    # 2. Test Discovery API - Get events from DB
    print("\n[2] EVENT DISCOVERY TEST")
    print("-" * 40)
    discovery = DiscoveryEngine()
    all_events = await discovery.get_all_events(limit=20)
    print(f"Events returned from get_all_events: {len(all_events)}")
    
    if all_events:
        print("\nFirst 5 events:")
        for e in all_events[:5]:
            has_detail = "YES" if e.metadata_json else "NO"
            print(f"  {e.slug}: {e.title_ar[:35]}... | venue: {e.venue_name} | detail: {has_detail}")
    
    # 3. Test API Client - Get real event details
    print("\n[3] API CLIENT TEST")
    print("-" * 40)
    api = WebookApiClient()
    
    if all_events:
        # Test with first READY event
        test_event = all_events[0]
        print(f"Testing event: {test_event.slug}")
        
        # Get event detail
        detail = await api.get_event_detail(test_event.slug)
        print(f"Event detail response keys: {list(detail.keys()) if detail else 'EMPTY'}")
        
        if detail:
            print(f"  - title: {detail.get('title', 'N/A')}")
            print(f"  - venue: {detail.get('venue', {}).get('name', 'N/A') if isinstance(detail.get('venue'), dict) else 'N/A'}")
            print(f"  - event_tickets: {len(detail.get('event_tickets', []))} items")
            print(f"  - ticket_packages: {len(detail.get('ticket_packages', []))} items")
    
    # 4. Test ticket fetching
    print("\n[4] TICKET FETCHING TEST")
    print("-" * 40)
    
    for i, event in enumerate(all_events[:3]):
        print(f"\nTesting event #{i+1}: {event.slug}")
        
        # Test via DiscoveryEngine
        tickets_data = await discovery.get_event_tickets_live(event.slug)
        print(f"  Tickets response keys: {list(tickets_data.keys())}")
        
        event_tickets = tickets_data.get("event_tickets", [])
        print(f"  event_tickets count: {len(event_tickets)}")
        
        # Check data structure
        if event_tickets:
            sample = event_tickets[0]
            print(f"  Sample ticket fields: {list(sample.keys())}")
            print(f"  Sample ticket: id={sample.get('_id') or sample.get('id')}, title={sample.get('title')}, price={sample.get('price')}")
        else:
            # Check if it's nested differently
            data = tickets_data.get("data", {})
            if data:
                print(f"  Nested data keys: {list(data.keys())}")
                nested_tickets = data.get("event_tickets") or data.get("ticket_packages")
                if nested_tickets:
                    print(f"  Found nested tickets: {len(nested_tickets)}")
    
    # 5. Test quick reserve flow
    print("\n[5] QUICK RESERVE FLOW TEST")
    print("-" * 40)
    
    from apps.bot.handlers import extract_ticket_list, ticket_has_available_inventory
    
    for i, event in enumerate(all_events[:3]):
        print(f"\nQuick reserve test #{i+1}: {event.slug}")
        
        tickets_data = await discovery.get_event_tickets_live(event.slug)
        tickets = extract_ticket_list(tickets_data)
        print(f"  Extracted tickets: {len(tickets)}")
        
        if tickets:
            print(f"  First ticket: {json.dumps(tickets[0], ensure_ascii=False)[:200]}")
            
            # Check inventory
            active_tickets = [t for t in tickets if ticket_has_available_inventory(t)]
            print(f"  Active (available) tickets: {len(active_tickets)}")
            
            if active_tickets:
                best = active_tickets[0]
                print(f"  Best ticket: {best.get('title')} - {best.get('price')} SAR")
    
    # 6. Test event detail view
    print("\n[6] EVENT DETAIL VIEW TEST")
    print("-" * 40)
    
    for i, event in enumerate(all_events[:3]):
        print(f"\nEvent detail #{i+1}: {event.slug}")
        
        # Get detail from API
        detail = await api.get_event_detail(event.slug)
        
        if detail:
            tickets = detail.get("ticket_packages") or detail.get("event_tickets") or []
            print(f"  Tickets in detail: {len(tickets)}")
            
            if tickets:
                for t in tickets[:3]:
                    print(f"    - {t.get('title')}: {t.get('price')} SAR")
    
    # 7. Test categories browsing
    print("\n[7] CATEGORIES BROWSING TEST")
    print("-" * 40)
    
    categories = await discovery.get_live_categories()
    print(f"Categories found: {len(categories)}")
    
    for cat in categories[:5]:
        events_in_cat = await discovery.get_events_by_genre(cat.slug)
        print(f"  {cat.slug}: {len(events_in_cat)} events")
    
    # 8. Check accounts
    print("\n[8] ACCOUNTS CHECK")
    print("-" * 40)
    async with AsyncSessionLocal() as db:
        stmt = select(AuthSession).limit(5)
        accounts = (await db.execute(stmt)).scalars().all()
        print(f"Accounts in DB: {len(accounts)}")
        for acc in accounts:
            print(f"  - {acc.email} | role: {acc.role} | health: {acc.health} | active: {acc.is_active}")
    
    print("\n" + "=" * 60)
    print("VALIDATION COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(run_live_validation())
