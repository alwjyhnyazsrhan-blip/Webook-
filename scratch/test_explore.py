import asyncio
from modules.webook.client import WebookApiClient

async def test_explore():
    api = WebookApiClient()
    # Try 'explore' as a possible master org
    res = await api.get_events_by_organization("explore", per_page=10, page=0)
    print(f"EXPLORE TOTAL: {res.get('total')}")
    print(f"EXPLORE EVENTS: {len(res.get('events', []))}")

if __name__ == "__main__":
    asyncio.run(test_explore())
