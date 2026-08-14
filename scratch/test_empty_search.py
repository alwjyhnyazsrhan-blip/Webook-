import asyncio
from modules.webook.client import WebookApiClient

async def test_global_empty_search():
    api = WebookApiClient()
    print("PROBING GLOBAL EMPTY SEARCH...")
    params = {
        "lang": "ar",
        "visible_in": "webook",
        "per_page": "100",
        "page": "1"
    }
    # Try searching for a space or empty string
    resp = await api._reuest("GET", f"{api.BASE_URL}/filter/events", params=params)
    if resp.status_code == 200:
        data = resp.json()
        total = data.get("data", {}).get("total", 0)
        print(f"  GLOBAL TOTAL: {total}")
        events = data.get("data", {}).get("data", [])
        print(f"  EVENTS RETURNED: {len(events)}")
        if events:
            print(f"  SAMPLE: {events[0].get('title')} ({events[0].get('slug')})")

if __name__ == "__main__":
    asyncio.run(test_global_empty_search())
