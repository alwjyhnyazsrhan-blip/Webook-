import asyncio
from core.database.postgres import AsyncSessionLocal
from database.models.discovery import LiveEvent
from sqlalchemy import select

async def f():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(LiveEvent).where(LiveEvent.title_ar.like('%\u0627\u0644\u062e\u0644\u0648\u062f%')).limit(1))
        e = res.scalar_one_or_none()
        if e:
            print(f"SLUG:{e.slug}|CHART:{e.chart_key}|EV:{e.event_key}|WORK:{e.workspace_key}|EAGLE:{e.eagle_eye_image}")
        else:
            print("NONE")

if __name__ == "__main__":
    asyncio.run(f())
