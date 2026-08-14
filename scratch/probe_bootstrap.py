import asyncio
from modules.webook.client import WebookApiClient

async def probe_bootstrap():
    api = WebookApiClient()
    paths = ["/bootstrap", "/config", "/initial-data", "/home-page", "/app-config"]
    for path in paths:
        url = f"{api.BASE_URL}{path}"
        print(f"PROBING: {url}")
        resp = await api._reuest("GET", url, params={"lang": "ar", "visible_in": "webook"})
        print(f"  STATUS: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print(f"  KEYS: {list(data.get('data', {}).keys())}")
            if 'home_page' in data.get('data', {}):
                print("  FOUND HOME_PAGE DATA")

if __name__ == "__main__":
    asyncio.run(probe_bootstrap())
