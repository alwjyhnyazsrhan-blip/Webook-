import asyncio, json
from core.database.postgres import AsyncSessionLocal
from database.repositories.account import AccountRepository
from modules.webook.client import WebookApiClient

async def main():
    async with AsyncSessionLocal() as db:
        acc_repo = AccountRepository(db)
        acc = await acc_repo.get_healthy_account()
        token = acc.bearer_token if acc else None
        print('Token:', bool(token))
        client = WebookApiClient(bearer_token=token)
        res = await client.get_event_detail('rsl-25-26-al-fateh-vs-al-najma-692735')
        print(json.dumps(res, ensure_ascii=False)[:1000])

asyncio.run(main())
