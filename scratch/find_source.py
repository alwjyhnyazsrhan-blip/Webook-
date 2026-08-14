import asyncio
from modules.webook.client import WebookApiClient

async def find_working_source():
    api = WebookApiClient()
    # Try the other token found in the codebase
    api.API_TOKEN = "ce492c7f756978ba98da0627544f69fbc76aae789bdab3f241d111d8642416db"
    sources = ["webook", "web", "mobile", "ios", "android", ""]
    for src in sources:
        print(f"TESTING SOURCE: '{src}'")
        api.APP_SOURCE = src
        res = await api.get_all_upcoming_events(per_page=10, page=1)
        events = res.get("events", [])
        total = res.get("total", 0)
        print(f"  -> RECEIVED: {len(events)} | TOTAL: {total}")
        if events:
            print(f"  !!! SUCCESS WITH SOURCE: {src}")

if __name__ == "__main__":
    asyncio.run(find_working_source())
