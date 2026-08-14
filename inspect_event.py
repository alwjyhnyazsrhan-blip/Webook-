import asyncio
import httpx
import json

async def inspect_event_detail():
    slug = "rsl-25-26-al-ahli-vs-al-kholood-05162026"
    url = f"https://api.webook.com/api/v2/event-detail/{slug}?lang=en"
    headers = {
        "X-App-Version": "1.4.66",
        "X-Client-Version": "1.4.66",
        "token": "e9aac1f2f0b6c07d6be070ed14829de684264278359148d6a582ca65a50934d2"
    }
    
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            # Look for season_id, organization_id, etc.
            print(f"Slug: {data.get('slug')}")
            print(f"ID: {data.get('id')}")
            print(f"Organization ID: {data.get('organization_id')}")
            print(f"Season ID: {data.get('season_id')}")
            print(f"Metadata: {data.get('metadata', {}).get('season_id')}")
            
            # Check for any other interesting fields
            print(f"All keys: {list(data.keys())}")
        else:
            print(f"Failed to fetch event detail: {resp.status_code}")

if __name__ == "__main__":
    asyncio.run(inspect_event_detail())
