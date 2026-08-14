import asyncio
from core.database.postgres import AsyncSessionLocal
from database.repositories.account import AccountRepository
from modules.webook.client import WebookApiClient

async def fetch_home_with_token():
    api = WebookApiClient()
    async with AsyncSessionLocal() as db:
        acc_repo = AccountRepository(db)
        account = await acc_repo.get_healthy_account()
        if not account:
            print("NO HEALTHY ACCOUNT FOUND")
            return
        
        token = account.bearer_token
        print(f"USING TOKEN: {token[:10]}...")
        
        # Try fetching home or explore
        paths = [
            "/home-page",
            "/home",
            "/explore",
            "/discover",
            "/config",
            "/organizations"
        ]
        
        for path in paths:
            url = f"{api.BASE_URL}{path}"
            print(f"PROBING: {url}")
            resp = await api._reuest("GET", url, params={"lang": "ar"}, authenticated=True)
            print(f"  STATUS: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                print(f"  SUCCESS! Keys: {list(data.get('data', {}).keys())}")
                if 'total' in data.get('data', {}):
                    print(f"  TOTAL reported: {data['data']['total']}")

if __name__ == "__main__":
    asyncio.run(fetch_home_with_token())
