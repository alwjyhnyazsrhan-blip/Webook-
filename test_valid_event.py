import asyncio
import json
from modules.webook.client import WebookApiClient

async def main():
    client = WebookApiClient()
    res = await client.get_event_tickets("improv-night-show-274410")
    tickets = res.get("event_tickets", [])
    if tickets:
        t = tickets[0]
        print(f"Title: {t.get('title')}")
        print(f"Remaining: {t.get('remaining')}")
        print(f"Sale Status: {t.get('sale_status')}")
        print(f"Sold Out: {t.get('sold_out')}")

asyncio.run(main())
