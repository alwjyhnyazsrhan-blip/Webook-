from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from core.database.postgres import AsyncSessionLocal
from database.repositories.reservation import ReservationRepository
from datetime import datetime, timezone
from database.models.discovery import LiveEvent, Genre
from sqlalchemy import select, func

router = APIRouter()
templates = Jinja2Templates(directory="apps/dashboard/templates")

@router.get("/")
async def index(request: Request):
    async with AsyncSessionLocal() as db:
        repo = ReservationRepository(db)
        tasks = await repo.get_active_tasks()
        
        # Fetch Events for the new UI
        events_stmt = select(LiveEvent).order_by(LiveEvent.synced_at.desc()).limit(100)
        events = (await db.execute(events_stmt)).scalars().all()
        
        # Fetch Genres for filtering
        genres_stmt = select(Genre).where(Genre.is_active == True)
        genres = (await db.execute(genres_stmt)).scalars().all()

        # Simple counts for metrics
        stats = {
            "total_events": (await db.execute(select(func.count(LiveEvent.id)))).scalar(),
            "ready_events": (await db.execute(select(func.count(LiveEvent.id)).where(LiveEvent.hydration_status == 'READY'))).scalar(),
            "discovered_events": (await db.execute(select(func.count(LiveEvent.id)).where(LiveEvent.hydration_status == 'DISCOVERED'))).scalar(),
            "failed_events": (await db.execute(select(func.count(LiveEvent.id)).where(LiveEvent.hydration_status == 'FAILED'))).scalar(),
            
            # Funnel Health (Replacing in-memory discovery_metrics)
            "categorized": (await db.execute(select(func.count(LiveEvent.id)).where(LiveEvent.genre_id != None))).scalar(),
            "uncategorized": (await db.execute(select(func.count(LiveEvent.id)).where(LiveEvent.genre_id == None))).scalar(),
            "hydrated": (await db.execute(select(func.count(LiveEvent.id)).where(LiveEvent.hydration_status == 'READY'))).scalar(),
            "403_failed": (await db.execute(select(func.count(LiveEvent.id)).where(LiveEvent.hydration_status == 'FAILED'))).scalar(),
            "duplicate_skipped": 0
        }

        return templates.TemplateResponse("index.html", {
            "request": request,
            "tasks": tasks,
            "events": events,
            "genres": genres,
            "stats": stats
        })

@router.get("/health")
async def health():
    return {"status": "healthy"}
