import asyncio

async def test_wwe_event():
    results = []
    
    def log(msg):
        results.append(str(msg))
        print(msg)
    
    log("=" * 60)
    log("FOCUS TEST: WWE EVENT (HAS AVAILABLE TICKETS)")
    log("=" * 60)
    
    from apps.bot.handlers import (
        extract_ticket_list, 
        ticket_has_available_inventory,
        _seatmap_payload
    )
    from services.discovery.engine import DiscoveryEngine
    
    discovery = DiscoveryEngine()
    slug = "tickets-wwe-experience"
    
    log(f"\n[1] Testing event: {slug}")
    
    # Get tickets via discovery engine (like handlers do)
    log("Fetching tickets via discovery.get_event_tickets_live()...")
    tickets_data = await discovery.get_event_tickets_live(slug)
    log(f"Response keys: {list(tickets_data.keys())}")
    
    # Extract tickets
    tickets = extract_ticket_list(tickets_data)
    log(f"Extracted tickets: {len(tickets)}")
    
    # Check inventory
    active = [t for t in tickets if ticket_has_available_inventory(t)]
    log(f"Available (active) tickets: {len(active)}")
    
    log("\n[2] Available Categories:")
    for t in active:
        log(f"  - {t.get('title')}")
        log(f"    Price: {t.get('price')} SAR")
        log(f"    Remaining: {t.get('remaining')}")
        log(f"    ID: {t.get('_id')}")
    
    log("\n[3] Quick Reserve Flow (simulating handle_speed_book):")
    if active:
        sorted_tickets = sorted(active, key=lambda x: float(x.get("price") or 9999))
        best = sorted_tickets[0]
        log(f"Quick reserve would select: {best.get('title')} at {best.get('price')} SAR")
        log(f"Ticket ID for reservation: {best.get('_id')}")
    
    log("\n[4] Full Category Selection Flow (simulating proceed_to_categories):")
    log(f"Would show {len(active)} categories to user:")
    for i, t in enumerate(active[:10]):
        log(f"  {i+1}. {t.get('title')}: {t.get('price')} SAR")
    
    log("\n[5] Seatmap Flow:")
    from modules.webook.client import WebookApiClient
    api = WebookApiClient()
    detail = await api.get_event_detail(slug)
    
    from core.database.postgres import AsyncSessionLocal
    from database.models.discovery import LiveEvent
    from sqlalchemy import select
    
    async with AsyncSessionLocal() as db:
        stmt = select(LiveEvent).where(LiveEvent.slug == slug)
        event = (await db.execute(stmt)).scalar_one_or_none()
        
        if event:
            payload = _seatmap_payload(event, detail)
            log(f"Has seatmap data: {payload.get('is_seated')}")
            log(f"Booking URL: {payload.get('booking_url')}")
            log(f"Has chart_key: {bool(payload.get('chart_key'))}")
    
    log("\n" + "=" * 60)
    log("FOCUS TEST COMPLETE - WWE EVENT HAS WORKING FLOW")
    log("=" * 60)
    
    with open("wwe_focus_test.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(results))

asyncio.run(test_wwe_event())
