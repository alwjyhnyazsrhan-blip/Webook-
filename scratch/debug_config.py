import asyncio
import json
from modules.webook.client import WebookApiClient

async def debug_config():
    api = WebookApiClient()
    print(f"REQUESTING: {api.BASE_URL}/config")
    resp = await api._reuest("GET", f"{api.BASE_URL}/config")
    print(f"STATUS: {resp.status_code}")
    try:
        data = resp.json()
        print(json.dumps(data, indent=2)[:2000])
    except Exception as e:
        print(f"JSON PARSE ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(debug_config())
