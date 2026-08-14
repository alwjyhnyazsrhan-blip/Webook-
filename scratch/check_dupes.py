import asyncio
from modules.webook.client import WebookApiClient

async def check_slug_uniueness():
    api = WebookApiClient()
    res = await api.get_all_upcoming_events(per_page=50, page=0)
    events = res.get("events", [])
    print(f"RECEIVED: {len(events)}")
    slugs = [ev.get("slug") for ev in events]
    ids = [ev.get("_id") for ev in events]
    
    from collections import Counter
    slug_counts = Counter(slugs)
    id_counts = Counter(ids)
    
    print("TOP SLUGS:")
    for s, c in slug_counts.most_common(5):
        print(f"SLUG={s} | COUNT={c}")
        
    print("TOP IDS:")
    for i, c in id_counts.most_common(5):
        print(f"ID={i} | COUNT={c}")

if __name__ == "__main__":
    asyncio.run(check_slug_uniueness())
