import asyncio
import httpx
from modules.auth.fingerprint import FingerprintGenerator

async def test_discovery():
    headers = FingerprintGenerator.generate()
    headers["Accept"] = "application/json"
    headers["Origin"] = "https://webook.com"
    headers["Referer"] = "https://webook.com/"
    
    async with httpx.AsyncClient(headers=headers, timeout=15) as client:
        # Try Genres
        print("Fetching Genres...")
        r = await client.get("https://api.webook.com/v1/discovery/genres")
        print(f"Genres Status: {r.status_code}")
        if r.status_code == 200:
            genres = r.json().get("data", [])
            print(f"Found {len(genres)} Genres.")
            for g in genres[:3]:
                print(f" - {g.get('name')} ({g.get('slug')})")
        else:
            print(f"Error: {r.text[:200]}")

        # Try Events
        print("\nFetching Events...")
        r = await client.get("https://api.webook.com/v1/discovery/events")
        print(f"Events Status: {r.status_code}")
        if r.status_code == 200:
            events = r.json().get("data", [])
            print(f"Found {len(events)} Events.")
            for ev in events[:5]:
                print(f" - {ev.get('name')} | ID: {ev.get('id')}")
        else:
            print(f"Error: {r.text[:200]}")

if __name__ == "__main__":
    asyncio.run(test_discovery())
