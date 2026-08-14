import asyncio
from modules.webook.client import WebookApiClient

async def test_slug_contexts():
    api = WebookApiClient()
    slug = "escape-it-rs-24"
    contexts = ["webook", "riyadh-season", "jeddah-season", "mobile-app", "web-app"]
    for ctx in contexts:
        print(f"TESTING '{slug}' IN CONTEXT: '{ctx}'")
        resp = await api._reuest("GET", f"{api.BASE_URL}/event-detail/{slug}", params={"lang": "ar", "visible_in": ctx})
        if resp.status_code == 200:
            data = resp.json()
            if data.get("data"):
                print(f"  SUCCESS! Title: {data['data'].get('title')}")
            else:
                print(f"  EMPTY DATA (200 OK but null data)")
        else:
            print(f"  STATUS: {resp.status_code}")

if __name__ == "__main__":
    asyncio.run(test_slug_contexts())
