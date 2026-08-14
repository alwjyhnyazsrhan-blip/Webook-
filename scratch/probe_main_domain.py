import asyncio
import httpx
from modules.auth.fingerprint import FingerprintGenerator

async def probe_main_domain():
    headers = FingerprintGenerator.generate()
    # Try hitting the API on the main domain
    url = "https://webook.com/api/v2/filter/events"
    params = {"lang": "ar", "visible_in": "webook", "per_page": "10"}
    
    print(f"PROBING MAIN DOMAIN: {url}")
    async with httpx.AsyncClient(headers=headers) as client:
        resp = await client.get(url, params=params)
        print(f"  STATUS: {resp.status_code}")
        if resp.status_code == 200:
            try:
                data = resp.json()
                print(f"  TOTAL: {data.get('data', {}).get('total')}")
            except:
                print(f"  FAILED TO DECODE JSON. TEXT: {resp.text[:200]}...")
        else:
            print(f"  BODY: {resp.text[:200]}...")

if __name__ == "__main__":
    asyncio.run(probe_main_domain())
