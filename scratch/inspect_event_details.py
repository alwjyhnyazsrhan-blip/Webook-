import asyncio
import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/.."))

from modules.webook.client import WebookApiClient

async def main():
    api = WebookApiClient()
    print("Fetching live event details from Webook API...")
    try:
        detail = await api.get_event_detail("spl-week-34-al-kholood-vs-al-fateh-9190")
        print("Success! Keys in detail:")
        print(list(detail.keys()))
        data_obj = detail.get("data", detail)
        print("Keys in data_obj:")
        print(list(data_obj.keys()))
        
        # Check seats_io or seats configuration
        seats_io = data_obj.get("seats_io") or data_obj.get("seats")
        print("seats_io / seats config:")
        print(json.dumps(seats_io, indent=2, ensure_ascii=False))
        
        # Check event_tickets packages
        tickets = data_obj.get("event_tickets") or data_obj.get("event_ticket") or data_obj.get("ticket_packages") or []
        print(f"Total tickets/packages found: {len(tickets)}")
        for t in tickets:
            print(f"Ticket: {t.get('ticket_title') or t.get('title')} | ID: {t.get('_id')} | Category: {t.get('category_key') or t.get('categoryKey')} | SeatsIoCategory: {t.get('seats_io_category') or t.get('seatsIoCategory')}")
    except Exception as e:
        print(f"API Fetch failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
