import asyncio
import json
from modules.webook.client import WebookApiClient

async def probe_keys():
    api = WebookApiClient()
    # Try to find an org that HAS events
    res = await api.get_all_upcoming_events(per_page=5, page=0)
    events = res.get("events", [])
    if events:
        print(f"FOUND EVENTS IN GLOBAL UPCOMING")
        print(f"KEYS: {list(events[0].keys())}")
        # Check for ID and SLUG specifically
        print(f"ID: {events[0].get('id')} | _ID: {events[0].get('_id')}")
        print(f"SLUG: {events[0].get('slug')} | URL_SLUG: {events[0].get('url_slug')}")
        return
    print("NO EVENTS FOUND IN ANY PROBED ORG")

if __name__ == "__main__":
    asyncio.run(probe_keys())
