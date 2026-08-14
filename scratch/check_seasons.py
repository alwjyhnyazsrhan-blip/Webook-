import asyncio
from modules.webook.client import WebookApiClient

async def check_seasons():
    api = WebookApiClient()
    res = await api.get_events_by_organization("riyadh-season", per_page=10, page=1)
    seasons = res.get("seasons", [])
    print(f"RIYADH SEASON -> SEASONS FOUND: {len(seasons)}")
    for s in seasons:
        print(f"  SEASON: {s.get('title')} | SLUG: {s.get('slug')}")

if __name__ == "__main__":
    asyncio.run(check_seasons())
