import httpx
import asyncio

async def probe_raw():
    url = "https://api.webook.com/api/v2/filter/events/webook"
    params = {
        "lang": "ar",
        "status": "upcoming",
        "per_page": "50"
    }
    headers = {
        "Accept": "application/json",
        "token": "e9aac1f2f0b6c07d6be070ed14829de684264278359148d6a582ca65a50934d2",
        "Origin": "https://webook.com",
        "Referer": "https://webook.com/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params, headers=headers)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            events = data.get("data", {}).get("data", [])
            print(f"Events: {len(events)}")
            print(f"Total: {data.get('data', {}).get('total', 0)}")
            if events:
                print(f"First event: {events[0].get('title')}")

if __name__ == "__main__":
    asyncio.run(probe_raw())
