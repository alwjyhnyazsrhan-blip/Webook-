import asyncio
import json
from modules.webook.client import WebookApiClient

async def test_season_events():
    api = WebookApiClient()
    # Use the WWE bundle slug from earlier
    slug = "wwe-two-nights-bundle-wwe-tickets--season--374653"
    print(f"REQUESTING EVENTS FOR SEASON: {slug}")
    # Try different V2 paths for season events
    paths = [
        f"/season-detail/{slug}/events",
        f"/filter/events/{slug}",
        f"/season/{slug}/events"
    ]
    for path in paths:
        url = f"{api.BASE_URL}{path}"
        print(f"  TRYING: {url}")
        resp = await api._reuest("GET", url, params={"lang": "ar"})
        print(f"  STATUS: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            events = data.get("data", {}).get("data", [])
            print(f"  SUCCESS! FOUND {len(events)} EVENTS")
            if events:
                print(f"  FIRST SUB-EVENT: {events[0].get('title')}")

if __name__ == "__main__":
    asyncio.run(test_season_events())
