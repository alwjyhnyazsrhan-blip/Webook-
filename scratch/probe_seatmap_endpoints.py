import asyncio
import json

import httpx
from sqlalchemy import select

from core.database.postgres import AsyncSessionLocal
from database.models.discovery import LiveEvent
from modules.webook.client import WebookApiClient


SLUGS = [
    "gfdgfsfg-ikhkihy7-8979g-9-9hatehr",
    "rsl-al-khaleej-vs-al-ettifa-363834",
    "riyadh-ettifa",
    "chinese-contemporary-art-exhibition",
]


def compact(value, limit=1800):
    return json.dumps(value, ensure_ascii=False, default=str)[:limit]


def find_keys(value, path=""):
    hits = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else key
            if any(name in key.lower() for name in ["seat", "chart", "map", "event_key", "chartkey", "chart_key", "token", "provider"]):
                hits.append((child_path, child))
            hits.extend(find_keys(child, child_path))
    elif isinstance(value, list):
        for i, child in enumerate(value):
            hits.extend(find_keys(child, f"{path}[{i}]"))
    return hits


async def api_get(client, path, **params):
    url = f"{client.BASE_URL}{path}"
    resp = await client._reuest("GET", url, params={"lang": "ar", "visible_in": "webook", **params})
    try:
        payload = resp.json()
    except Exception:
        payload = resp.text[:500]
    print("ENDPOINT", path, "STATUS", resp.status_code, "KEYS", list(payload.keys()) if isinstance(payload, dict) else type(payload).__name__)
    for hit_path, value in find_keys(payload):
        print("  HIT", hit_path, compact(value, 900))
    return payload


async def main():
    client = WebookApiClient()
    async with AsyncSessionLocal() as db:
        for slug in SLUGS:
            event = (await db.execute(select(LiveEvent).where(LiveEvent.slug == slug))).scalar_one_or_none()
            print("EVENT", slug, event.id if event else None, event.title_ar if event else None)
            meta = event.metadata_json if event and isinstance(event.metadata_json, dict) else {}
            for hit_path, value in find_keys(meta):
                print("  DB_HIT", hit_path, compact(value, 700))
            await api_get(client, f"/event-detail/{slug}")
            await api_get(client, f"/event-ticket-details/{slug}")
            await api_get(client, f"/event-detail/{slug}/availability")
            print("----")

    # Probe common Seats.io renderer/static URLs with a known slug-shaped value.
    async with httpx.AsyncClient(timeout=15, follow_redirects=False) as hc:
        for url in [
            "https://cdn.seatsio.net/chart.js",
            "https://cdn-eu.seatsio.net/chart.js",
            "https://cdn-sa.seatsio.net/chart.js",
        ]:
            resp = await hc.get(url)
            print("SEATS_CDN", url, resp.status_code, resp.headers.get("content-type"), resp.text[:120])


if __name__ == "__main__":
    asyncio.run(main())

