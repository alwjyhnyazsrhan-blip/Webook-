import asyncio
from modules.webook.client import WebookApiClient

async def main():
    client = WebookApiClient()
    res = await client.get_event_detail("spl-week-34-al-kholood-vs-al-fateh-9190")
    import json
    with open("webook_event.json", "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)

asyncio.run(main())
