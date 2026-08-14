import asyncio
import json
from modules.webook.client import WebookApiClient

async def debug_events_v2():
    api = WebookApiClient()
    # Try the most logical endpoint for all events in V2
    print(f"REQUESTING: {api.BASE_URL}/events")
    resp = await api._reuest("GET", f"{api.BASE_URL}/events", params={"lang": "ar", "per_page": 50})
    print(f"STATUS: {resp.status_code}")
    try:
        data = resp.json()
        print(f"TOTAL: {data.get('total')}")
        events = data.get('data', [])
        if not events and 'data' in data and isinstance(data['data'], dict):
             events = data['data'].get('data', [])
        print(f"RECEIVED: {len(events)}")
        if events:
            print(f"FIRST SLUG: {events[0].get('slug')}")
    except Exception as e:
        print(f"JSON PARSE ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(debug_events_v2())
