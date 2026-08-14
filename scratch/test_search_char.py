import asyncio
from modules.webook.client import WebookApiClient

async def test_search_char():
    api = WebookApiClient()
    # Search for common character
    params = {"lang": "ar", "search": "\u0627", "per_page": "100"}
    resp = await api._reuest("GET", f"{api.BASE_URL}/filter/events", params=params)
    if resp.status_code == 200:
        data = resp.json()
        total = data.get("data", {}).get("total", 0)
        print(f"SEARCH '\u0627' TOTAL: {total}")
        
    params = {"lang": "en", "search": "a", "per_page": "100"}
    resp = await api._reuest("GET", f"{api.BASE_URL}/filter/events", params=params)
    if resp.status_code == 200:
        data = resp.json()
        total = data.get("data", {}).get("total", 0)
        print(f"SEARCH 'a' TOTAL: {total}")

if __name__ == "__main__":
    asyncio.run(test_search_char())
