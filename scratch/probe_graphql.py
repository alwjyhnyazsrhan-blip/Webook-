import asyncio
import httpx
from modules.webook.client import WebookApiClient

async def probe_graphl():
    api = WebookApiClient()
    # Common GraphQL paths
    paths = ["/graphl", "/api/graphl", "/api/v2/graphl", "/api/v1/graphl"]
    for path in paths:
        url = f"https://api.webook.com{path}"
        print(f"PROBING: {url}")
        try:
            # Try a simple introspection uery or a dummy uery
            uery = {"uery": "{ __schema { types { name } } }"}
            resp = await api._reuest("POST", url, json=uery)
            print(f"  STATUS: {resp.status_code}")
            if resp.status_code == 200:
                print(f"  !!! FOUND GRAPHQL AT {url}")
                return
        except Exception as e:
            print(f"  FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(probe_graphl())
