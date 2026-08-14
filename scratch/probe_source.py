import httpx
import asyncio

async def probe_source():
    url = "https://api.webook.com/api/v2/filter/events/webook"
    headers = {
        "Accept": "application/json",
        "token": "e9aac1f2f0b6c07d6be070ed14829de684264278359148d6a582ca65a50934d2",
        "Origin": "https://webook.com",
        "Referer": "https://webook.com/"
    }
    
    for source in ["web", "webook"]:
        params = {
            "lang": "ar",
            "status": "upcoming",
            "per_page": "50",
            "visible_in": source
        }
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, params=params, headers=headers)
            if resp.status_code == 200:
                total = resp.json().get("data", {}).get("total", 0)
                print(f"Source '{source}' -> Total: {total}")
            else:
                print(f"Source '{source}' -> Error: {resp.status_code}")

if __name__ == "__main__":
    asyncio.run(probe_source())
