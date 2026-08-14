import asyncio
import json

async def test_full_ticket_flow():
    results = []
    
    def log(msg):
        results.append(str(msg))
    
    log("=" * 60)
    log("FULL TICKET EXTRACTION FLOW TEST")
    log("=" * 60)
    
    # Import the actual bot code
    from services.discovery.engine import DiscoveryEngine
    from apps.bot.handlers import extract_ticket_list, ticket_has_available_inventory
    
    discovery = DiscoveryEngine()
    
    # Test with the known working event
    test_slugs = [
        "tickets-wwe-experience",  # Has tickets
        "house-of-hype",  # Might not have tickets
    ]
    
    for slug in test_slugs:
        log(f"\n--- Testing: {slug} ---")
        
        # 1. Get tickets via DiscoveryEngine
        log("Step 1: Get tickets via discovery.get_event_tickets_live")
        tickets_data = await discovery.get_event_tickets_live(slug)
        log(f"  Response keys: {list(tickets_data.keys())}")
        
        # 2. Extract ticket list
        log("Step 2: extract_ticket_list()")
        tickets = extract_ticket_list(tickets_data)
        log(f"  Extracted {len(tickets)} tickets")
        
        if tickets:
            log(f"  First ticket sample: {json.dumps(tickets[0], ensure_ascii=False)[:150]}")
        
        # 3. Check inventory
        log("Step 3: ticket_has_available_inventory()")
        active_tickets = [t for t in tickets if ticket_has_available_inventory(t)]
        log(f"  Active (available) tickets: {len(active_tickets)}")
        
        if active_tickets:
            log("  Available tickets:")
            for t in active_tickets[:3]:
                log(f"    - {t.get('title')}: {t.get('price')} SAR (remaining: {t.get('remaining')})")
        
        # 4. Test via direct API
        log("Step 4: Direct API test")
        from modules.webook.client import WebookApiClient
        api = WebookApiClient()
        detail = await api.get_event_detail(slug)
        
        if detail:
            event_tickets = detail.get("event_tickets", [])
            ticket_packages = detail.get("ticket_packages", [])
            log(f"  Direct - event_tickets: {len(event_tickets)}")
            log(f"  Direct - ticket_packages: {len(ticket_packages)}")
    
    log("\n" + "=" * 60)
    log("TEST COMPLETE")
    log("=" * 60)
    
    with open("full_flow_test.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(results))
    print("Results in full_flow_test.txt")

asyncio.run(test_full_ticket_flow())
