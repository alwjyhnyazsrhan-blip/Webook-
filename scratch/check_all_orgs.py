import asyncio
from modules.webook.client import WebookApiClient

async def check_all_orgs():
    api = WebookApiClient()
    print("FETCHING ORGANIZATIONS...")
    res = await api.get_organizations(limit=100)
    orgs = res.get("data", {}).get("data", [])
    print(f"TOTAL ORGANIZATIONS IN API: {len(orgs)}")
    for o in orgs[:10]:
        print(f"  ORG: {o.get('name')} | SLUG: {o.get('slug')}")
    
    # Save all slugs to a file for comparison
    with open("scratch/api_org_slugs.txt", "w") as f:
        for o in orgs:
            f.write(f"{o.get('slug')}\n")

if __name__ == "__main__":
    asyncio.run(check_all_orgs())
