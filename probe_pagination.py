import asyncio
from modules.webook.client import WebookApiClient
import json

async def probe_pagination():
    client = WebookApiClient()
    all_events = []
    
    # Ø§ÙØªØ­ÙÙ ÙÙ Ø§ÙÙ€ Global Discovery ÙØ¹ Pagination ÙÙØ«Ù
    print("--- PROBING GLOBAL DISCOVERY ---")
    for page in range(1, 10):
        print(f"Reuesting Global Page {page}...")
        res = await client.get_all_upcoming_events(page=page, per_page=50)
        events = res.get("events", [])
        print(f"Page {page} returned {len(events)} events.")
        if not events:
            print(f"Stopping at page {page} - No more events.")
            break
        all_events.extend(events)

    print(f"\nTOTAL GLOBAL EVENTS DISCOVERED: {len(all_events)}")
    
    # Ø§ÙØªØ­ÙÙ ÙÙ Ø§ÙÙ€ Organizations Ø§ÙÙÙÙÙØ¯Ø©
    print("\n--- PROBING ORGANIZATIONS ---")
    orgs_to_test = ["riyadh-season", "jeddah-season", "saudi-pro-league", "general-entertainment-authority"]
    for org in orgs_to_test:
        print(f"Reuesting Org: {org} Page 1...")
        res = await client.get_events_by_organization(org, page=1, per_page=50)
        events = res.get("events", [])
        print(f"Org {org} returned {len(events)} events.")

if __name__ == "__main__":
    asyncio.run(probe_pagination())
