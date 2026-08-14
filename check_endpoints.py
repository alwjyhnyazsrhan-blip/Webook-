import asyncio
import httpx
import json

async def check_endpoints():
    slug = "rsl-25-26-al-ahli-vs-al-kholood-05162026"
    base = "https://api.webook.com/api/v2"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "X-App-Version": "1.4.66",
        "X-Client-Version": "1.4.66",
        "token": "e9aac1f2f0b6c07d6be070ed14829de684264278359148d6a582ca65a50934d2",
        "Accept": "application/json",
        "Origin": "https://webook.com",
        "Referer": "https://webook.com/"
    }
    
    urls = [
        f"{base}/event-detail/{slug}/event-seat/checkout",
        f"{base}/reservations",
        f"{base}/event-detail/{slug}/checkout"
    ]
    
    async with httpx.AsyncClient() as client:
        for url in urls:
            # We use OPTIONS to check if the endpoint exists and what it expects
            try:
                resp = await client.options(url, headers=headers)
                print(f"URL: {url} | Status: {resp.status_code}")
            except Exception as e:
                print(f"URL: {url} | Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_endpoints())
