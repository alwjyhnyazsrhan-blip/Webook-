import asyncio
import httpx
import json

async def run_validation():
    results = []
    
    def log(msg):
        results.append(str(msg))
    
    log("=" * 60)
    log("WEOOK LIVE API VALIDATION")
    log("=" * 60)
    
    headers = {
        "Accept": "application/json",
        "Origin": "https://webook.com",
        "Referer": "https://webook.com/",
        "token": "e9aac1f2f0b6c07d6be070ed14829de684264278359148d6a582ca65a50934d2"
    }
    
    async with httpx.AsyncClient(headers=headers, timeout=30) as client:
        # Test 1: Get events from riyadh-season
        log("\n[TEST 1] Events from riyadh-season")
        r = await client.get("https://api.webook.com/api/v2/organizations/riyadh-season/events?lang=ar&status=upcoming&page=1&per_page=10")
        log(f"Status: {r.status_code}")
        
        if r.status_code == 200:
            data = r.json()
            events = data.get("data", {}).get("data", [])
            log(f"Found {len(events)} events")
            
            for ev in events[:5]:
                slug = ev.get("slug", "N/A")
                title = str(ev.get("title", "N/A"))[:50]
                log(f"  - {slug}: {title}")
        
        # Test 2: Get event detail for first event
        log("\n[TEST 2] Event Detail API")
        if r.status_code == 200:
            data = r.json()
            events = data.get("data", {}).get("data", [])
            if events:
                test_slug = events[0].get("slug")
                log(f"Testing event: {test_slug}")
                
                r = await client.get(f"https://api.webook.com/api/v2/events/{test_slug}?lang=ar")
                log(f"Status: {r.status_code}")
                
                if r.status_code == 200:
                    detail = r.json().get("data", {})
                    log(f"Detail keys: {list(detail.keys())}")
                    
                    # Check for tickets
                    tickets = detail.get("event_tickets", [])
                    log(f"event_tickets count: {len(tickets)}")
                    
                    ticket_packages = detail.get("ticket_packages", [])
                    log(f"ticket_packages count: {len(ticket_packages)}")
                    
                    all_tickets = tickets or ticket_packages
                    if all_tickets:
                        sample = all_tickets[0]
                        log(f"Sample ticket keys: {list(sample.keys())}")
                        log(f"Sample: id={sample.get('_id') or sample.get('id')}, title={sample.get('title')}, price={sample.get('price')}")
                    
                    # Check venue
                    venue = detail.get("venue", {})
                    if isinstance(venue, dict):
                        log(f"Venue: {venue.get('name')}")
        
        # Test 3: Get sports events
        log("\n[TEST 3] Sports Events (saudi-pro-league)")
        r = await client.get("https://api.webook.com/api/v2/organizations/saudi-pro-league/events?lang=ar&status=upcoming&page=1&per_page=5")
        log(f"Status: {r.status_code}")
        
        if r.status_code == 200:
            data = r.json()
            sports_events = data.get("data", {}).get("data", [])
            log(f"Found {len(sports_events)} sports events")
            
            for ev in sports_events[:3]:
                slug = ev.get("slug", "N/A")
                log(f"  Testing: {slug}")
                
                # Get detail to check tickets
                r2 = await client.get(f"https://api.webook.com/api/v2/events/{slug}?lang=ar")
                if r2.status_code == 200:
                    detail = r2.json().get("data", {})
                    tix = detail.get("event_tickets", []) or detail.get("ticket_packages", [])
                    log(f"    Tickets: {len(tix)}")
                    if tix:
                        for t in tix[:2]:
                            log(f"      - {t.get('title')}: {t.get('price')} SAR")
        
        # Test 4: Get music events
        log("\n[TEST 4] Music Events (mdl-beast)")
        r = await client.get("https://api.webook.com/api/v2/organizations/mdl-beast/events?lang=ar&status=upcoming&page=1&per_page=5")
        log(f"Status: {r.status_code}")
        
        if r.status_code == 200:
            data = r.json()
            music_events = data.get("data", {}).get("data", [])
            log(f"Found {len(music_events)} music events")
            
            for ev in music_events[:3]:
                slug = ev.get("slug", "N/A")
                log(f"  Testing: {slug}")
                
                # Check tickets
                r2 = await client.get(f"https://api.webook.com/api/v2/events/{slug}?lang=ar")
                if r2.status_code == 200:
                    detail = r2.json().get("data", {})
                    tix = detail.get("event_tickets", []) or detail.get("ticket_packages", [])
                    log(f"    Tickets: {len(tix)}")
                    if tix:
                        for t in tix[:2]:
                            log(f"      - {t.get('title')}: {t.get('price')} SAR")
        
        # Test 5: Get all upcoming events across orgs
        log("\n[TEST 5] All upcoming events")
        all_events = []
        orgs = ["riyadh-season", "saudi-pro-league", "mdl-beast", "jeddah-season", "diriyah-season"]
        
        for org in orgs:
            try:
                r = await client.get(f"https://api.webook.com/api/v2/organizations/{org}/events?lang=ar&status=upcoming&page=1&per_page=10")
                if r.status_code == 200:
                    data = r.json()
                    events = data.get("data", {}).get("data", [])
                    all_events.extend(events)
                    log(f"{org}: {len(events)} events")
            except Exception as e:
                log(f"{org}: error - {e}")
        
        log(f"Total events across all orgs: {len(all_events)}")
        
        # Test 6: Check event with tickets
        log("\n[TEST 6] Find event with available tickets")
        for ev in all_events[:10]:
            slug = ev.get("slug")
            r = await client.get(f"https://api.webook.com/api/v2/events/{slug}?lang=ar")
            if r.status_code == 200:
                detail = r.json().get("data", {})
                tix = detail.get("event_tickets", []) or detail.get("ticket_packages", [])
                if tix:
                    log(f"Found event with tickets: {slug}")
                    for t in tix:
                        log(f"  - {t.get('title')}: {t.get('price')} SAR (remaining: {t.get('remaining')})")
                    break
    
    log("\n" + "=" * 60)
    log("VALIDATION COMPLETE")
    log("=" * 60)
    
    # Write results to file
    with open("validation_output.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(results))
    print("Results written to validation_output.txt")

if __name__ == "__main__":
    asyncio.run(run_validation())
