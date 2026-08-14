import asyncio
from modules.webook.client import WebookApiClient

async def test_experience_endpoint():
    api = WebookApiClient()
    slug = "doos-karting"
    prefixes = ["event-detail", "experience-detail", "restaurant-detail", "package-detail", "detail"]
    for prefix in prefixes:
        url = f"{api.BASE_URL}/{prefix}/{slug}"
        print(f"PROBING: {url}")
        resp = await api._reuest("GET", url, params={"lang": "ar", "visible_in": "webook"})
        print(f"  STATUS: {resp.status_code}")
        if resp.status_code == 200:
            print(f"  !!! FOUND VALID ENDPOINT: {prefix}")
            break

if __name__ == "__main__":
    asyncio.run(test_experience_endpoint())
