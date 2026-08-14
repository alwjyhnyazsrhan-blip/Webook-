import asyncio
from modules.webook.client import WebookApiClient

async def test_zone_api():
    api = WebookApiClient()
    slug = "boulevard-city"
    prefixes = ["event-detail", "zone-detail", "zone"]
    for p in prefixes:
        url = f"{api.BASE_URL}/{p}/{slug}"
        print(f"PROBING ZONE: {url}")
        resp = await api._reuest("GET", url, params={"lang": "ar", "visible_in": "webook"})
        if resp.status_code == 200:
            print(f"  SUCCESS! Prefix: {p}")
            data = resp.json()
            # Look for sub-events
            evs = data.get("data", {}).get("events", [])
            print(f"  SUB-EVENTS FOUND: {len(evs)}")
            for ev in evs[:5]:
                print(f"    - {ev.get('title')} ({ev.get('slug')})")

if __name__ == "__main__":
    asyncio.run(test_zone_api())
