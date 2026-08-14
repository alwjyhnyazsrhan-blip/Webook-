import asyncio
import json
from modules.webook.client import WebookApiClient

async def probe_webook_0():
    api = WebookApiClient()
    # Use 'webook' as organizationSlug, page=0
    res = await api.get_events_by_organization("webook", per_page=50, page=0)
    print(f"Org webook Page 0: {len(res.get('events', []))} events. Total: {res.get('total', 0)}")
    
    # Try global without slug, page=0
    res = await api.get_all_upcoming_events(per_page=50, page=0)
    print(f"Global Page 0: {len(res.get('events', []))} events. Total: {res.get('total', 0)}")

if __name__ == "__main__":
    asyncio.run(probe_webook_0())
