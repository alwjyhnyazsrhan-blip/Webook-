import asyncio
from modules.webook.client import WebookApiClient

async def test_statuses():
    api = WebookApiClient()
    statuses = ["upcoming", "active", "available", "live", "all", "completed"]
    for s in statuses:
        print(f"TESTING STATUS: '{s}'")
        params = {
            "lang": "ar",
            "visible_in": "webook",
            "status": s,
            "page": "1",
            "per_page": "10",
        }
        resp = await api._reuest("GET", f"{api.BASE_URL}/filter/events/riyadh-season", params=params)
        if resp.status_code == 200:
            total = resp.json().get("data", {}).get("total", 0)
            print(f"  -> TOTAL: {total}")

if __name__ == "__main__":
    asyncio.run(test_statuses())
