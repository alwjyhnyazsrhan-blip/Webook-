import asyncio
import sys
import os

# Add root folder to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/.."))

from modules.webook.client import WebookApiClient

async def main():
    c = WebookApiClient()
    print("Testing event songsofthemountains-7jun...")
    try:
        res = await c.get_event_detail("songsofthemountains-7jun")
        print("Detail status:", res.get("status"))
        data = res.get("data") or {}
        print("Detail keys:", list(data.keys()))
        print("event_tickets:", data.get("event_tickets"))
        print("event_ticket:", data.get("event_ticket"))
        print("ticket_packages:", data.get("ticket_packages"))
        print("tickets:", data.get("tickets"))
    except Exception as e:
        print("ERROR:", e)

if __name__ == "__main__":
    asyncio.run(main())
