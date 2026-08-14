import asyncio
from modules.webook.client import WebookApiClient
import json

async def test_org():
    client = WebookApiClient()
    print("Fetching Riyadh Season events...")
    res = await client.get_events_by_organization(org_slug="riyadh-season")
    print(f"Org Result: {json.dumps(res, indent=2)}")

if __name__ == "__main__":
    asyncio.run(test_org())
