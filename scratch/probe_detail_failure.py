import asyncio
import json
import time

from sqlalchemy import select, func

from core.database.postgres import AsyncSessionLocal
from database.models.discovery import Genre, LiveEvent
from modules.webook.client import WebookApiClient


def keys(value):
    if isinstance(value, dict):
        return sorted(value.keys())
    return type(value).__name__


def compact(value, limit=500):
    text = json.dumps(value, ensure_ascii=False, default=str)
    return text[:limit] + ("..." if len(text) > limit else "")


async def main():
    async with AsyncSessionLocal() as db:
        rows = (await db.execute(
            select(LiveEvent, Genre.slug)
            .join(Genre, LiveEvent.genre_id == Genre.id, isouter=True)
            .where(
                (func.lower(LiveEvent.title_ar).like("%helicopter%"))
                | (func.lower(LiveEvent.slug).like("%helicopter%"))
                | (LiveEvent.title_ar.like("%ï¿½ï¿½ï¿½ï¿½%"))
                | (LiveEvent.title_ar.like("%\u0627ï¿½\u0627\u062a\u0641\u0627ï¿½%"))
                | (func.lower(LiveEvent.slug).like("%neom%"))
                | (func.lower(LiveEvent.slug).like("%ettifa%"))
            )
            .limit(20)
        )).all()

        print("DB_MATCHES=", len(rows))
        for event, genre_slug in rows:
            meta = event.metadata_json or {}
            contentful = meta.get("contentful") if isinstance(meta, dict) else None
            print("ROW", {
                "id": event.id,
                "slug": event.slug,
                "webook_id": event.webook_id,
                "title": event.title_ar,
                "status": event.status,
                "hydration_status": event.hydration_status,
                "attempts": event.hydration_attempts,
                "last_error": event.last_hydration_error,
                "genre": genre_slug,
                "starts_at": event.starts_at,
                "venue_name": event.venue_name,
                "image": bool(event.image_url),
                "meta_keys": keys(meta),
                "contentful_keys": keys(contentful),
            })
            if isinstance(meta, dict):
                for name in ["venue", "location", "zone", "city", "schedule", "home_team", "away_team", "teams", "competitors"]:
                    if name in meta:
                        print("  META", name, compact(meta.get(name)))
            if isinstance(contentful, dict):
                for name in ["location", "schedule", "category"]:
                    if name in contentful:
                        print("  CONTENTFUL", name, compact(contentful.get(name)))

        status_rows = (await db.execute(
            select(LiveEvent.hydration_status, func.count(LiveEvent.id))
            .group_by(LiveEvent.hydration_status)
        )).all()
        print("HYDRATION_COUNTS=", [(status, count) for status, count in status_rows])

    client = WebookApiClient()
    for event, _ in rows[:8]:
        start = time.perf_counter()
        try:
            detail = await asyncio.wait_for(client.get_event_detail(event.slug), timeout=15)
            print("API_DETAIL", {
                "slug": event.slug,
                "elapsed_ms": round((time.perf_counter() - start) * 1000, 1),
                "empty": not bool(detail),
                "keys": keys(detail),
            })
            if isinstance(detail, dict):
                for name in ["venue", "location", "zone", "city", "schedule", "start_date_time", "startDate", "endDate", "home_team", "away_team", "teams", "competitors"]:
                    if name in detail:
                        print("  API", name, compact(detail.get(name)))
        except Exception as exc:
            print("API_DETAIL_EXCEPTION", event.slug, type(exc).__name__, str(exc))


if __name__ == "__main__":
    asyncio.run(main())

