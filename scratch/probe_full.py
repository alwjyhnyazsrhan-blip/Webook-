import asyncio
import httpx
import json

async def probe_full():
    url = "https://api.webook.com/api/v2/filter/events/webook"
    params = {"lang": "ar", "status": "upcoming", "per_page": "50", "visible_in": "webook"}
    headers = {
        "token": "e9aac1f2f0b6c07d6be070ed14829de684264278359148d6a582ca65a50934d2",
        "Accept": "application/json"
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params, headers=headers)
        print(f"STATUS: {resp.status_code}")
        if resp.status_code == 200:
            with open("scratch/full_api_response.json", "w", encoding="utf-8") as f:
                json.dump(resp.json(), f, indent=2, ensure_ascii=False)
            print("Response saved to scratch/full_api_response.json")

if __name__ == "__main__":
    asyncio.run(probe_full())
