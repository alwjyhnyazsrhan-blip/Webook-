import asyncio
from core.database.postgres import AsyncSessionLocal
from database.models.reservation import AuthSession, ReservationTask, TaskStatus
from core.logging.logger import setup_logging, logger
from datetime import datetime, timedelta, timezone

async def seed_trial_data():
    setup_logging()
    logger.info("Seeding Trial Data (Dashboard Visualization)...")
    
    async with AsyncSessionLocal() as db:
        # 1. Add an Active Session
        session = AuthSession(
            email="trial_master@webook.com",
            bearer_token="TRIAL_TOKEN_123",
            device_token="DEVICE_123",
            proxy_url="http://trial:proxy@localhost:8080",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Sniper/1.0"
        )
        db.add(session)
        
        # 2. Add some 'Mock' successful tasks to see in dashboard
        task = ReservationTask(
            user_id=999,
            event_slug="trial-match-2026",
            category="VIP",
            status=TaskStatus.SUCCESS.value,
            hold_token="HOLD-TRIAL-777",
            hold_expires_at=datetime.now(timezone.utc) + timedelta(minutes=8),
            logs=[{"t": str(datetime.now(timezone.utc)), "msg": "Elite Sniper Trial: Success!"}]
        )
        db.add(task)
        
        await db.commit()
    logger.info("Trial Data Seeded Successfully.")

if __name__ == "__main__":
    asyncio.run(seed_trial_data())
