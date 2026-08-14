
import asyncio
import asyncpg
import os
from datetime import datetime, timezone
import uuid

async def simulate_concurrency_stress():
    db_url = os.getenv("DATABASE_URL", "postgresl://admin:admin@db:5432/webook")
    if "+asyncpg" in db_url: db_url = db_url.replace("+asyncpg", "")
    
    print("--- CONCURRENCY STRESS TEST (Postgres Row Locking) ---")
    
    conn = await asyncpg.connect(db_url)
    
    # 1. Create a dummy task
    task_id = await conn.fetchval("""
        INSERT INTO reservation_tasks (event_slug, status, created_at)
        VALUES ('concurrency-test-event', 'QUEUED', $1)
        RETURNING id
    """, datetime.now(timezone.utc))
    
    print(f"Created Task ID: {task_id}")
    
    # 2. Simulate 5 concurrent workers trying to claim the same task
    # We will use 'FOR UPDATE' in a transaction
    
    async def worker_claim(worker_name):
        try:
            # We need a NEW connection per worker for true concurrency
            w_conn = await asyncpg.connect(db_url)
            async with w_conn.transaction():
                print(f"[{worker_name}] Attempting lock...")
                # The 'FOR UPDATE' will block others
                row = await w_conn.fetchrow("""
                    SELECT id, status FROM reservation_tasks 
                    WHERE id = $1 AND status = 'QUEUED' 
                    FOR UPDATE SKIP LOCKED
                """, task_id)
                
                if row:
                    print(f"[{worker_name}] LOCK ACQUIRED! Processing...")
                    # Simulate processing time
                    await asyncio.sleep(2)
                    await w_conn.execute("UPDATE reservation_tasks SET status = 'PROCESSING' WHERE id = $1", task_id)
                    print(f"[{worker_name}] DONE. Status updated to PROCESSING.")
                    return True
                else:
                    print(f"[{worker_name}] Lock failed or task already claimed.")
                    return False
            await w_conn.close()
        except Exception as e:
            print(f"[{worker_name}] Error: {e}")
            return False

    # Run 5 workers simultaneously
    results = await asyncio.gather(*[worker_claim(f"Worker-{i}") for i in range(5)])
    
    # Verify only ONE worker succeeded
    success_count = sum(1 for r in results if r)
    print(f"\nFinal Audit: {success_count} worker(s) successfully claimed the task.")
    
    if success_count == 1:
        print("âœ SUCCESS: Row-level locking prevented duplicate processing.")
    else:
        print(f"âŒ FAILURE: {success_count} workers processed the same task!")

    await conn.close()

if __name__ == "__main__":
    asyncio.run(simulate_concurrency_stress())
