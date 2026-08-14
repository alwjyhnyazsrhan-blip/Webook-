import asyncio
import json
from modules.webook.client import WebookApiClient

async def probe_structure():
    api = WebookApiClient()
    res = await api.get_all_upcoming_events(per_page=50, page=0)
    events = res.get("events", [])
    if events:
        print(json.dumps(events[0], indent=2, ensure_ascii=False))
    else:
        print("NO EVENTS FOUND")

if __name__ == "__main__":
    asyncio.run(probe_structure())
