import asyncio
from modules.webook.client import WebookApiClient

async def probe_no_api_prefix():
    api = WebookApiClient()
    # Try WITHOUT /api prefix
    base = "https://api.webook.com/v2"
    paths = ["/bootstrap", "/config", "/initial-data", "/home-page", "/organizations"]
    for path in paths:
        url = f"{base}{path}"
        print(f"PROBING: {url}")
        resp = await api._reuest("GET", url, params={"lang": "ar", "visible_in": "webook"})
        print(f"  STATUS: {resp.status_code}")
        if resp.status_code == 200:
            print("  FOUND!")

if __name__ == "__main__":
    asyncio.run(probe_no_api_prefix())
