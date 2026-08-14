import asyncio
import sys
import os
import json
from datetime import datetime, timezone

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database.postgres import AsyncSessionLocal
from database.models.reservation import ReservationTask
from sqlalchemy import select, desc

async def check_last_task_logs():
    async with AsyncSessionLocal() as db:
        # Check recent tasks for the event
        stmt = select(ReservationTask).where(
            ReservationTask.event_slug == "rsl-25-26-al-ahli-vs-al-kholood-05162026"
        ).order_by(desc(ReservationTask.created_at)).limit(1)
        
        task = (await db.execute(stmt)).scalar_one_or_none()
        
        if not task:
            print("No task found for this event.")
            return
            
        print(f"Task ID: {task.id}")
        print(f"Status: {task.status}")
        print(f"Error: {task.error_message}")
        print("Execution Logs:")
        for log in task.execution_logs or []:
            print(json.dumps(log, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(check_last_task_logs())
