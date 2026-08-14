import asyncio
import json
import httpx
import sys
import os

# Add the project root to sys.path
sys.path.append(os.getcwd())

from modules.webook.client import WebookApiClient

async def main():
    client = WebookApiClient()
    slug = "rsl-25-26-al-ahli-vs-al-kholood-05162026"
    try:
        resp = await client.get_event_detail(slug)
        data = resp.get("data", {})
        seats_io = data.get("seats_io") or data.get("seats") or {}
        print("SEATS_IO METADATA:")
        print(json.dumps(seats_io, indent=2))
        
        # Also check categories to see which category 10 belongs to
        tickets = data.get("event_tickets", [])
        for t in tickets:
            print(f"Ticket: {t.get('title')} | Key: {t.get('category_key')} | SeatsIO Category: {t.get('seats_io_category')}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
