import asyncio
import httpx
from modules.auth.fingerprint import FingerprintGenerator

async def probe_discovery_api():
    headers = FingerprintGenerator.generate()
    base = "https://api.webook.com/api/v2"
    
    # Try different discovery paths
    paths = [
        "/filter/events",
        "/events",
        "/search",
        "/home",
        "/explore",
        "/discover"
    ]
    
    for path in paths:
        url = f"{base}{path}"
        print(f"PROBING: {url}")
        params = {"lang": "ar", "visible_in": "webook"}
        async with httpx.AsyncClient(headers=headers) as client:
            resp = await client.get(url, params=params)
            print(f"  STATUS: {resp.status_code}")
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    total = data.get("data", {}).get("total", 0)
                    print(f"  SUCCESS! Total: {total}")
                except:
                    print("  FAILED TO DECODE JSON")

if __name__ == "__main__":
    asyncio.run(probe_discovery_api())
