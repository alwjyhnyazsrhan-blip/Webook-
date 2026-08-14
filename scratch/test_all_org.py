import asyncio
from modules.webook.client import WebookApiClient

async def test_all_org():
    api = WebookApiClient()
    # Try 'all' as a possible master org
    res = await api.get_events_by_organization("all", per_page=10, page=1)
    print(f"ALL TOTAL: {res.get('total')}")
    print(f"ALL EVENTS: {len(res.get('events', []))}")

if __name__ == "__main__":
    asyncio.run(test_all_org())
