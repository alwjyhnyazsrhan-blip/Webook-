import asyncio
from modules.webook.client import WebookApiClient

async def test_no_filter():
    api = WebookApiClient()
    # Test filter/events/riyadh-season WITHOUT visible_in
    params = {
        "lang": "ar",
        "status": "upcoming",
        "page": "1",
        "per_page": "50",
    }
    url = f"{api.BASE_URL}/filter/events/riyadh-season"
    print(f"REQUESTING: {url} (NO FILTER)")
    resp = await api._reuest("GET", url, params=params)
    data = resp.json()
    print(f"TOTAL: {data.get('data', {}).get('total', 0)}")
    
    # Test search WITHOUT visible_in
    print("SEARCHING 'riyadh' (NO FILTER)")
    resp = await api._reuest("GET", f"{api.BASE_URL}/search", params={"uery": "riyadh", "lang": "ar"})
    data = resp.json()
    print(f"SEARCH TOTAL: {len(data.get('data', {}).get('events', []))}")

if __name__ == "__main__":
    asyncio.run(test_no_filter())
