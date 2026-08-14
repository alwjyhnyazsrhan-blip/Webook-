import asyncio
import sys
import os

# Add root folder to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/.."))

from core.database.postgres import AsyncSessionLocal
from database.models.reservation import ReservationTask, TaskStatus
from database.models.account import AuthSession
from services.reservation.orchestrator import ReservationOrchestrator

async def run_live_snipe():
    print("=" * 60)
    print("LIVE SNIPE EXECUTION AUDIT (REAL EVENT & ACCOUNT)")
    print("=" * 60)
    
    # 1. Verify we have the account and get its ID
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        stmt = select(AuthSession).where(AuthSession.email == 'sypherdox@gmail.com')
        res = await db.execute(stmt)
        account = res.scalar_one_or_none()
        
    if not account:
        print("[-] FAILED: Account sypherdox@gmail.com not found!")
        return
        
    print(f"[+] Active Sniper Account found: {account.email} (ID: {account.id})")
    
    # 2. Trigger the task via ReservationOrchestrator
    async with AsyncSessionLocal() as db:
        orch = ReservationOrchestrator(db)
        
        # Live active event details:
        slug = "songsofthemountains-7jun"
        category_id = "69fca6abf50b2efacb0eb24f" # Ticket 'GP' ID we saw in step 2
        
        print(f"\n[+] Initializing live task for slug={slug}, ticket_id={category_id}...")
        task = await orch.start_reservation(
            user_id=1,
            slug=slug,
            category_id=category_id,
            count=1
        )
        task_id = task.id
        print(f"[+] Task successfully created and queued! Task ID: {task_id}")
        
    # 3. Monitor execution status and logs in real-time
    print("\n[+] Monitoring background worker execution (20s timeout)...")
    for i in range(20):
        await asyncio.sleep(1)
        async with AsyncSessionLocal() as db:
            updated_task = await db.get(ReservationTask, task_id)
            if updated_task:
                print(f"    - [{i+1}s] Status: {updated_task.status} | Hold Token: {updated_task.hold_token or 'None'}")
                if updated_task.status in [TaskStatus.SUCCESS.value, TaskStatus.FAILED.value]:
                    print(f"\n[+] Worker completed execution with status: {updated_task.status}")
                    if updated_task.error_message:
                        print(f"[-] Error: {updated_task.error_message}")
                    
                    print("\n[+] Detailed Execution Logs:")
                    for log in updated_task.execution_logs or []:
                        print(f"    - [{log.get('ts')}] {log.get('msg') or log.get('action') or ''} {log.get('error') or ''}")
                    break
    else:
        print("[-] Timeout: Task did not complete in 20 seconds.")

if __name__ == "__main__":
    asyncio.run(run_live_snipe())
