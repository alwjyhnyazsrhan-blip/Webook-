import asyncio
from modules.webook.client import WebookApiClient
import json

async def test_detail():
    client = WebookApiClient()
    slug = "rsl-25-26-neom-vs-al-shabab-11052026"
    print(f"Fetching detail for {slug}...")
    res = await client.get_event_detail(slug)
    print(f"Detail Result: {json.dumps(res, indent=2)}")

if __name__ == "__main__":
    asyncio.run(test_detail())
