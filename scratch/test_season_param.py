import asyncio
from modules.webook.client import WebookApiClient

async def test_season_slug_param():
    api = WebookApiClient()
    # Use the WWE bundle slug
    slug = "wwe-two-nights-bundle-wwe-tickets--season--374653"
    print(f"PROBING SEASON SLUG PARAM FOR: {slug}")
    
    # Try different param combinations
    params_list = [
        {"season_slug": slug, "lang": "ar"},
        {"season": slug, "lang": "ar"},
        {"event_group_slug": slug, "lang": "ar"},
    ]
    
    for params in params_list:
        print(f"  PARAMS: {params}")
        resp = await api._reuest("GET", f"{api.BASE_URL}/filter/events", params=params)
        if resp.status_code == 200:
            data = resp.json()
            events = data.get("data", {}).get("data", [])
            print(f"    STATUS: 200 | FOUND: {len(events)} EVENTS")
            if events:
                print(f"    FIRST EVENT: {events[0].get('title')}")
        else:
            print(f"    STATUS: {resp.status_code}")

if __name__ == "__main__":
    asyncio.run(test_season_slug_param())
