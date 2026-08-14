import asyncio
import json
from modules.webook.client import WebookApiClient

async def main():
    client = WebookApiClient()
    # Using the live client to fetch tickets
    tickets_data = await client.get_event_tickets("spl-week-34-al-hazem-vs-al-taawoun-3710")
    print(json.dumps(tickets_data, ensure_ascii=False, indent=2))

asyncio.run(main())
