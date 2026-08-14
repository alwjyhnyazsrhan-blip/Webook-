import asyncio
import json
from modules.webook.client import WebookApiClient

async def debug_raw_api():
    api = WebookApiClient()
    # Try the most common endpoint
    params = {
        "lang": "ar",
        "visible_in": "webook",
        "status": "upcoming",
        "page": "1",
        "per_page": "10",
    }
    print(f"REQUESTING: {api.BASE_URL}/filter/events")
    resp = await api._reuest("GET", f"{api.BASE_URL}/filter/events", params=params)
    print(f"STATUS: {resp.status_code}")
    try:
        print(f"RAW BODY: {resp.text[:1000]}")
        data = resp.json()
        print(f"PARSED KEYS: {list(data.keys())}")
        if "data" in data:
            print(f"DATA KEYS: {list(data['data'].keys())}")
    except Exception as e:
        print(f"JSON PARSE ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(debug_raw_api())
