import asyncio
import json
from modules.webook.client import WebookApiClient

async def check_real_categories():
    slug = "spl-week-34-al-hazem-vs-al-taawoun-3710"
    api = WebookApiClient()
    print(f"Fetching categories for {slug}...")
    data = await api.get_event_detail(slug)
    
    if not data:
        print("Failed to fetch event detail.")
        return

    print(f"Event Title: {data.get('title')}")
    print(f"Is Seated: {data.get('is_seated')}")
    print(f"Is Soldout (API): {data.get('is_soldout')}")
    print(f"API Status: {data.get('status')}")
    
    tickets = data.get("event_tickets") or data.get("ticket_packages") or []
    print(f"Found {len(tickets)} categories")
    for t in tickets:
        remaining = t.get("remaining") or t.get("available") or 0
        print(f"  - {t.get('title')} (ID: {t.get('_id') or t.get('id')}) | Remaining: {remaining}")

if __name__ == "__main__":
    asyncio.run(check_real_categories())
