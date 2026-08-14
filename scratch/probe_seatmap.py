import asyncio
import json

from sqlalchemy import func, select

from core.database.postgres import AsyncSessionLocal
from database.models.discovery import LiveEvent
from services.discovery.engine import DiscoveryEngine


def compact(value, limit=1200):
    return json.dumps(value, ensure_ascii=False, default=str)[:limit]


def find_keys(value, names=None, path=""):
    names = names or ("seats", "chart", "map", "token", "key", "io")
    hits = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else key
            if any(name in key.lower() for name in names):
                hits.append((child_path, child))
            hits.extend(find_keys(child, names, child_path))
    elif isinstance(value, list):
        for i, child in enumerate(value):
            hits.extend(find_keys(child, names, f"{path}[{i}]"))
    return hits


async def main():
    engine = DiscoveryEngine()
    async with AsyncSessionLocal() as db:
        rows = (
            await db.execute(
                select(LiveEvent)
                .where((LiveEvent.stadium_map_url != None) | (LiveEvent.chart_token != None))
                .limit(20)
            )
        ).scalars().all()
        print("CHART_ROWS=", len(rows))
        for event in rows[:10]:
            meta = event.metadata_json if isinstance(event.metadata_json, dict) else {}
            chart = event.stadium_map_url or event.chart_token or engine._find_chart_token_recursive(meta)
            print("EVENT", {
                "id": event.id,
                "slug": event.slug,
                "title": event.title_ar,
                "chart_token": event.chart_token,
                "stadium_map_url": event.stadium_map_url,
                "chart": chart,
                "meta_keys": sorted(meta.keys())[:80],
            })
            for path, value in find_keys(meta):
                print("  HIT", path, compact(value, 900))

        total = (
            await db.execute(
                select(func.count(LiveEvent.id)).where((LiveEvent.stadium_map_url != None) | (LiveEvent.chart_token != None))
            )
        ).scalar()
        print("TOTAL_WITH_CHART=", total)


if __name__ == "__main__":
    asyncio.run(main())

