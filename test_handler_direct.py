import asyncio
import json
import sys

# Set up path for imports
sys.path.insert(0, '/app')

async def test_handler_flow():
    results = []
    
    def log(msg):
        results.append(str(msg))
        print(msg)
    
    log("=" * 60)
    log("DIRECT HANDLER FLOW TEST (SIMULATING TELEGRAM)")
    log("=" * 60)
    
    # Import handlers directly
    from apps.bot.handlers import (
        extract_ticket_list, 
        ticket_has_available_inventory,
        _seatmap_payload
    )
    from services.discovery.engine import DiscoveryEngine
    
    discovery = DiscoveryEngine()
    
    # Test 1: Get events like the bot does
    log("\n[TEST 1] Simulating handle_start - get_all_events")
    events = await discovery.get_all_events(limit=10)
    log(f"Found {len(events)} READY events")
    
    if not events:
        log("No READY events - triggering sync")
        await discovery.sync_all()
        events = await discovery.get_all_events(limit=10)
        log(f"After sync: {len(events)} events")
    
    # Test 2: Event detail flow (simulating e_det callback)
    log("\n[TEST 2] Simulating event detail fetch")
    if events:
        test_event = events[0]
        log(f"Testing event: {test_event.slug}")
        
        # Get detail like handle_event_detail does
        from modules.webook.client import WebookApiClient
        api = WebookApiClient()
        detail = await api.get_event_detail(test_event.slug)
        log(f"Detail keys: {list(detail.keys()) if detail else 'None'}")
        
        # Extract fields
        from apps.bot.handlers import extract_detail_fields, extract_team_options
        
        fields = extract_detail_fields(detail, test_event)
        log(f"Extracted title: {fields.get('title', 'N/A')[:50]}")
        log(f"Extracted venue: {fields.get('venue', 'N/A')}")
        
        # Extract tickets
        tickets = detail.get("ticket_packages") or detail.get("event_tickets") or []
        log(f"Tickets from detail: {len(tickets)}")
        
        # If no tickets in detail, fetch live
        if not tickets:
            log("Fetching live tickets...")
            tickets_data = await discovery.get_event_tickets_live(test_event.slug)
            tickets = extract_ticket_list(tickets_data)
            log(f"Live tickets: {len(tickets)}")
    
    # Test 3: Category selection (simulating proceed_to_categories)
    log("\n[TEST 3] Simulating category selection")
    if events:
        test_event = events[0]
        slug = test_event.slug
        
        # Get tickets
        tickets_data = await discovery.get_event_tickets_live(slug)
        tickets = extract_ticket_list(tickets_data)
        log(f"Tickets extracted: {len(tickets)}")
        
        # Filter available
        active_tickets = [t for t in tickets if ticket_has_available_inventory(t)]
        log(f"Available tickets: {len(active_tickets)}")
        
        if active_tickets:
            log("Available categories:")
            for t in active_tickets[:5]:
                log(f"  - {t.get('title')}: {t.get('price')} SAR (remaining: {t.get('remaining', 'N/A')})")
    
    # Test 4: Quick reserve flow (simulating handle_speed_book)
    log("\n[TEST 4] Simulating quick reserve flow")
    if events:
        test_event = events[0]
        slug = test_event.slug
        
        tickets_data = await discovery.get_event_tickets_live(slug)
        tickets = extract_ticket_list(tickets_data)
        
        if tickets:
            active_tickets = [t for t in tickets if ticket_has_available_inventory(t)]
            
            if active_tickets:
                # Sort by price (cheapest first)
                sorted_tickets = sorted(active_tickets, key=lambda x: float(x.get("price") or x.get("base_price") or 9999))
                best = sorted_tickets[0]
                
                log(f"Quick reserve selected: {best.get('title')} at {best.get('price')} SAR")
                log(f"  Ticket ID: {best.get('_id') or best.get('id')}")
                log(f"  Remaining: {best.get('remaining')}")
            else:
                log("No available tickets for quick reserve")
    
    # Test 5: Seatmap payload generation
    log("\n[TEST 5] Simulating seatmap payload")
    if events:
        test_event = events[0]
        
        # Get detail for seatmap data
        from modules.webook.client import WebookApiClient
        api = WebookApiClient()
        detail = await api.get_event_detail(test_event.slug)
        
        # Generate payload
        payload = _seatmap_payload(test_event, detail)
        log(f"Seatmap payload:")
        log(f"  - provider: {payload.get('provider')}")
        log(f"  - is_seated: {payload.get('is_seated')}")
        log(f"  - static_image: {bool(payload.get('static_image'))}")
        log(f"  - chart_key: {payload.get('chart_key')}")
        log(f"  - event_key: {payload.get('event_key')}")
        log(f"  - workspace_key: {payload.get('workspace_key')}")
        log(f"  - booking_url: {payload.get('booking_url')}")
    
    # Test 6: Test with multiple events
    log("\n[TEST 6] Testing multiple events for consistency")
    for i, event in enumerate(events[:3]):
        slug = event.slug
        
        # Get tickets
        tickets_data = await discovery.get_event_tickets_live(slug)
        tickets = extract_ticket_list(tickets_data)
        active = [t for t in tickets if ticket_has_available_inventory(t)]
        
        log(f"Event {i+1} ({slug}): {len(tickets)} total, {len(active)} available")
    
    log("\n" + "=" * 60)
    log("HANDLER FLOW TEST COMPLETE")
    log("=" * 60)
    
    # Write results
    with open("handler_flow_test.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(results))
    print("\nResults in handler_flow_test.txt")

# Run in the Docker environment
asyncio.run(test_handler_flow())
