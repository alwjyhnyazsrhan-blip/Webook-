import asyncio
import json
from modules.webook.client import WebookApiClient

async def probe_webook():
    api = WebookApiClient()
    # Use 'webook' as organizationSlug
    res = await api.get_events_by_organization("webook", per_page=50, page=1)
    print(f"Org webook Page 1: {len(res.get('events', []))} events. Total: {res.get('total', 0)}")

if __name__ == "__main__":
    asyncio.run(probe_webook())
