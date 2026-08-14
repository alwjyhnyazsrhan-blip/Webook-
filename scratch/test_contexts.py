import asyncio
from modules.webook.client import WebookApiClient

async def test_app_contexts():
    api = WebookApiClient()
    contexts = ["webook", "riyadh-season", "jeddah-season", "mobile-app", "web-app"]
    for ctx in contexts:
        print(f"TESTING APP CONTEXT: '{ctx}'")
        params = {
            "lang": "ar",
            "visible_in": ctx,
            "status": "upcoming",
            "page": "1",
            "per_page": "10",
        }
        # Try both global filter and org filter
        resp = await api._reuest("GET", f"{api.BASE_URL}/filter/events/riyadh-season", params=params)
        if resp.status_code == 200:
            total = resp.json().get("data", {}).get("total", 0)
            print(f"  -> TOTAL (riyadh-season filter): {total}")

if __name__ == "__main__":
    asyncio.run(test_app_contexts())
