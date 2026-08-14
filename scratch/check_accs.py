import asyncio
from core.database.postgres import AsyncSessionLocal
from database.models.account import AuthSession
from sqlalchemy import select

async def run():
    async with AsyncSessionLocal() as db:
        accs = (await db.execute(select(AuthSession))).scalars().all()
        print(f"TOTAL ACCOUNTS IN DB: {len(accs)}")
        for a in accs:
            print(f" - {a.email} ({a.health}) | Token: {bool(a.bearer_token)}")

if __name__ == "__main__":
    asyncio.run(run())

