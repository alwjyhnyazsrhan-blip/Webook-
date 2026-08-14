import asyncio
import os
import sys
import json
from datetime import datetime, timezone

# Add parent dir to path
sys.path.append(os.getcwd())

# Force UTF-8 for stdout
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from core.database.engine import AsyncSessionLocal
from database.models.discovery import LiveEvent, Genre
from modules.webook.client import WebookApiClient
from sqlalchemy import select

async def main():
    user_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiI2NzhmYmQ3MDRiMTk1NTg5MTEwYzczZDIiLCJqdGkiOiJmMmI2YWFiYmNlMzNkZjY2MTMzNDEyMGQyYWQzYTZlMGIwYzU2YjI4NzE0NzYwMDE5MGEyNWU5MWFkMDAzODQ2ZWYzMzBiYWIzMDc4MWVjZiIsImlhdCI6MTc3ODE0MjI2Ni4wMDIzODIsIm5iZiI6MTc3ODE0MjI2Ni4wMDIzODQsImV4cCI6MTc3ODc0NzA2NS45OTg3MTUsInN1YiI6IjY5ZjdkN2IyNzVlYjJiY2ZmMTAxYjE3ZiIsInNjb3BlcyI6W119.GaRqwMWoxbBgYrbaxYmD9e-8Rew-LoNpE5xNsQnMcyHSY1plJXm8MuLeHUidAjwMYqzhrxMHF_P5SJ5Guktlz4Oodpye3bp06C4CIJpVYca8VX8uT71bj1WXdxzDWVCHI8nROdNmpna2ektF4wWV3PFsnOo23gM2axhQkBiiLrZz_pV_Z8tF5Kbl6LB98nV3ADewfC0aJNlQsAUvp6RDHlNAud26ZLO03SVv2XKXPPaPfOArQS8jmWxtbXi0vWTszQKnKY5-fRtm-25tMISZKWL10-TY0P1nPDUnn7T1vSVMC5eITLoZ1MnnFD0DQ3JBe9MEQM5JWz0_kcPBYrl3qfQk9h_7pUHVeIIyvma2ZDfYb87mPJAeV5Yja1C-0F2aDkmBancwR7MoD0Vnm6qpwH3SNh2NLoclSAmJ8a1oKlR1ViM1h7WrJXrVh6Z9wahm9saozgLT87bG4nKyl-IV7qjckzXbef6tZZSIBVJBW0xYT4utcTjdCYyxuZKrNy2xTggPbJVvOPrU3kVqiRZbjm75gwp0f88TdoP6bO40gkgr5B66G26DC_TS6FGEdC4jxs1dGUD_hGmOQJoeo-K0UuCOa1KzT_MX9QAfzPK7YSoWxsiTshtynKShnT0JKkYObs-vRcbyo6SWaRCUJH6HheSEOt0z-oVUi1Fbqt--MWM"
    slug = "rsl-al-shabab-vs-al-ittihad-149965"
    api = WebookApiClient(bearer_token=user_token)
    
    print(f"Syncing {slug}...")
    try:
        # Use more headers for parity
        res = await api.get_event_detail(slug)
    except Exception as e:
        print(f"API Error: {e}")
        return

    if not res or res.get("status") != "success":
        print(f"Failed status: {res.get('status')}")
        return

    data = res.get("data", {})
    webook_id = data.get("_id")
    
    async with AsyncSessionLocal() as db:
        org_slug = data.get("organization", {}).get("slug", "al-shabab")
        stmt = select(Genre).where(Genre.slug == org_slug)
        genre = (await db.execute(stmt)).scalar_one_or_none()
        if not genre:
            genre = Genre(name_ar=org_slug, name_en=org_slug, slug=org_slug, is_active=True)
            db.add(genre)
            await db.flush()
        
        stmt = select(LiveEvent).where(LiveEvent.slug == slug)
        event = (await db.execute(stmt)).scalar_one_or_none()
        if not event:
            event = LiveEvent(slug=slug, webook_id=webook_id)
            db.add(event)
        
        event.title_ar = data.get("title")
        event.title_en = data.get("title")
        event.genre_id = genre.id
        event.status = "AVAILABLE"
        event.hydration_status = "READY"
        
        start_ts = data.get("start_date_time")
        if start_ts:
            event.starts_at = datetime.fromtimestamp(int(start_ts), tz=timezone.utc)
        
        event.venue_name = data.get("venue_name")
        event.image_url = data.get("poster")
        event.metadata_json = data
        
        await db.commit()
        print(f"SUCCESS: {slug} is now in DB.")

if __name__ == "__main__":
    asyncio.run(main())
