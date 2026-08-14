import asyncio
from modules.webook.client import WebookApiClient

async def count_all_org_events():
    api = WebookApiClient()
    # List from DiscoveryEngine
    ORGS = [
        "webook", "riyadh-season", "jeddah-season", "diriyah-season",
        "saudi-pro-league", "mdl-beast", "general-entertainment-authority"
    ]
    for org in ORGS:
        res = await api.get_events_by_organization(org, per_page=1, page=0)
        total = res.get("total", 0)
        print(f"ORG: {org:30} | TOTAL API EVENTS: {total}")

if __name__ == "__main__":
    asyncio.run(count_all_org_events())
