import asyncio
from modules.webook.client import WebookApiClient
import json

async def test_search():
    client = WebookApiClient()
    print("Searching for 'Riyadh'...")
    res = await client.search_events(uery="Riyadh")
    print(f"Search Result: {json.dumps(res, indent=2)}")

if __name__ == "__main__":
    asyncio.run(test_search())
