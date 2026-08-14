
import asyncio
import asyncpg
import os

async def verify_postgres_persistence():
    db_url = os.getenv("DATABASE_URL", "postgresl://admin:admin@db:5432/webook")
    if "+asyncpg" in db_url: db_url = db_url.replace("+asyncpg", "")
    
    print(f"--- POSTGRES PERSISTENCE AUDIT ---")
    try:
        conn = await asyncpg.connect(db_url)
        
        # 1. Check Accounts
        count = await conn.fetchval("SELECT count(*) FROM auth_sessions")
        print(f"Accounts in DB: {count}")
        
        # 2. Check Tasks
        task_count = await conn.fetchval("SELECT count(*) FROM reservation_tasks")
        print(f"Tasks in DB: {task_count}")
        
        # 3. Check Live Events (Verification of migration)
        event_count = await conn.fetchval("SELECT count(*) FROM live_events")
        print(f"Events in DB: {event_count}")
        
        await conn.close()
    except Exception as e:
        print(f"Persistence Audit FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(verify_postgres_persistence())
