import asyncio
from modules.webook.client import WebookApiClient

async def test_zone_filter():
    api = WebookApiClient()
    slug = "boulevard-city"
    print(f"PROBING FILTER BY ZONE: {slug}")
    params = {"lang": "ar", "visible_in": "webook", "zone_slug": slug}
    resp = await api._reuest("GET", f"{api.BASE_URL}/filter/events", params=params)
    if resp.status_code == 200:
        data = resp.json()
        total = data.get("data", {}).get("total", 0)
        print(f"  TOTAL EVENTS IN ZONE: {total}")
        events = data.get("data", {}).get("data", [])
        for ev in events[:5]:
            print(f"    - {ev.get('title')} ({ev.get('slug')})")

if __name__ == "__main__":
    asyncio.run(test_zone_filter())
