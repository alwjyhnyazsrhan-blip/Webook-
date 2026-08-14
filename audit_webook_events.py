import asyncio
import httpx
import json

async def audit():
    # 1. Fetch Riyadh Season events from Webook API (Public)
    url = "https://api.webook.com/api/v2/organizations/riyadh-season/events?lang=ar&status=upcoming&page=1&per_page=50"
    headers = {
        "Accept": "application/json",
        "token": "e9aac1f2f0b6c07d6be070ed14829de684264278359148d6a582ca65a50934d2",
        "Origin": "https://webook.com",
        "Referer": "https://webook.com/ar",
    }
    
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers)
        if resp.status_code != 200:
            print(f"FAILED to fetch Riyadh Season: {resp.status_code}")
            return
            
        data = resp.json().get("data", {}).get("data", [])
        print(f"Found {len(data)} events in Riyadh Season on Webook API")
        
        for ev in data[:5]:
            slug = ev.get("slug")
            title = ev.get("title")
            # Fetch tickets for this event
            t_url = f"https://api.webook.com/api/v2/events/{slug}?lang=ar"
            t_resp = await client.get(t_url, headers=headers)
            t_data = t_resp.json().get("data", {})
            tickets = t_data.get("event_tickets") or t_data.get("ticket_packages") or []
            print(f"  Event: {title} ({slug}) | Tickets: {len(tickets)}")
            for t in tickets[:3]:
                t_title = t.get("title")
                t_id = t.get("_id")
                print(f"    - {t_title} (ID: {t_id})")

if __name__ == "__main__":
    asyncio.run(audit())
