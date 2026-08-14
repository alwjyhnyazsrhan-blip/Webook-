import asyncio
from core.database.postgres import AsyncSessionLocal
from database.models.account import AuthSession
from sqlalchemy import select

async def check():
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(AuthSession))
            accounts = result.scalars().all()
            print(f"ACCOUNTS_COUNT:{len(accounts)}")
            for acc in accounts:
                print(f"Account: {acc.email}, Role: {acc.role}, Health: {acc.health}")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(check())
