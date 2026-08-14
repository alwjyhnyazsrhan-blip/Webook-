import asyncio
from modules.webook.client import WebookApiClient
import json

async def dump_zone_json():
    api = WebookApiClient()
    slug = "boulevard-city"
    url = f"{api.BASE_URL}/event-detail/{slug}"
    resp = await api._reuest("GET", url, params={"lang": "ar", "visible_in": "webook"})
    if resp.status_code == 200:
        data = resp.json()
        print(f"ZONE KEYS: {list(data.get('data', {}).keys())}")
        # Look for any list of events
        for k, v in data.get('data', {}).items():
            if isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict):
                print(f"  FOUND LIST: {k} ({len(v)} items)")
                if 'slug' in v[0]:
                    print(f"    - First item slug: {v[0].get('slug')}")

if __name__ == "__main__":
    asyncio.run(dump_zone_json())
