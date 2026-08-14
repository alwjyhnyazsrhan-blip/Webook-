import asyncio

from sqlalchemy import func, select

from core.database.postgres import AsyncSessionLocal
from database.models.discovery import LiveEvent


async def main():
    async with AsyncSessionLocal() as db:
        total = (await db.execute(select(func.count(LiveEvent.id)))).scalar()
        rows = (
            await db.execute(
                select(LiveEvent.hydration_status, func.count(LiveEvent.id))
                .group_by(LiveEvent.hydration_status)
            )
        ).all()
        print("TOTAL=", total)
        print("HYDRATION_COUNTS=", [(status, count) for status, count in rows])


if __name__ == "__main__":
    asyncio.run(main())

