import asyncio
from core.database.postgres import AsyncSessionLocal
from database.models.reservation import AuthSession
from modules.auth.fingerprint import FingerprintGenerator
from core.logging.logger import setup_logging, logger

async def seed_accounts():
    setup_logging()
    logger.info("Seeding test accounts into the pool...")
    
    async with AsyncSessionLocal() as db:
        # Check if already seeded
        from sqlalchemy import select
        result = await db.execute(select(AuthSession))
        if result.scalars().first():
            logger.info("Accounts already exist. Skipping seed.")
            return

        test_accounts = [
            ("acc1@test.com", "http://user:pass@proxy1:8080"),
            ("acc2@test.com", "http://user:pass@proxy2:8080"),
            ("acc3@test.com", None), # Direct connection
        ]
        
        for email, proxy in test_accounts:
            acc = AuthSession(
                email=email,
                bearer_token=f"TOKEN_{email}",
                device_token="STANDARD_TOKEN",
                proxy_url=proxy,
                user_agent=FingerprintGenerator.generate()["User-Agent"],
                is_active=True
            )
            db.add(acc)
            logger.info(f"Seeded account: {email}")
            
        await db.commit()
    logger.info("Seeding SUCCESS.")

if __name__ == "__main__":
    asyncio.run(seed_accounts())

