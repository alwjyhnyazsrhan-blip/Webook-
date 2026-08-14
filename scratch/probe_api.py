import asyncio
import json
from modules.webook.client import WebookApiClient

async def probe():
    api = WebookApiClient()
    
    # 1. Probe Global Upcoming
    print("PROBING GLOBAL UPCOMING...")
    res = await api.get_all_upcoming_events(per_page=50, page=1)
    print(f"Global Page 1: {len(res.get('events', []))} events. Total: {res.get('total', 0)}")
    
    # 2. Probe specific orgs
    orgs = ["riyadh-season", "jeddah-season", "diriyah-season"]
    for org in orgs:
        res = await api.get_events_by_organization(org, per_page=50, page=1)
        print(f"Org {org}: {len(res.get('events', []))} events. Total: {res.get('total', 0)}")

    # 3. Probe with different status?
    # Maybe 'upcoming' is not enough.
    
if __name__ == "__main__":
    asyncio.run(probe())
