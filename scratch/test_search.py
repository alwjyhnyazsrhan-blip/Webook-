import asyncio
from modules.webook.client import WebookApiClient

async def test_search_discovery():
    api = WebookApiClient()
    ueries = ["a", "riyadh", "jeddah", "match", "concert"]
    for  in ueries:
        print(f"SEARCHING FOR: '{}'")
        res = await api.search_events()
        print(f"  -> FOUND: {len(res)} events")
        if res:
            print(f"  FIRST SLUG: {res[0].get('slug')}")

if __name__ == "__main__":
    asyncio.run(test_search_discovery())
