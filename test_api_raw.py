import asyncio
from modules.webook.client import WebookApiClient
from core.logging.logger import logger
import json

async def test_api():
    client = WebookApiClient()
    print("Fetching events...")
    res = await client.get_all_upcoming_events(per_page=10)
    print(f"API Result: {json.dumps(res, indent=2)}")
    
    events = res.get("events", [])
    print(f"Number of events returned: {len(events)}")

if __name__ == "__main__":
    asyncio.run(test_api())
