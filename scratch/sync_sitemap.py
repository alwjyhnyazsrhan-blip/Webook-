import asyncio
import httpx
import re
import xml.etree.ElementTree as ET
from core.database.postgres import AsyncSessionLocal
from database.models.discovery import LiveEvent, Genre
from sqlalchemy import select
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SitemapSync")

SITEMAP_INDEX = "https://webook.com/sitemap.xml"

async def get_xml(url: str):
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=30)
        return resp.text

async def extract_slugs_from_sitemap(url: str):
    logger.info(f"Processing sitemap: {url}")
    try:
        xml_content = await get_xml(url)
        # Handle namespaces
        root = ET.fromstring(xml_content)
        namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        
        slugs = set()
        for url_tag in root.findall('ns:url', namespace):
            loc = url_tag.find('ns:loc', namespace).text
            # Patterns: 
            # https://webook.com/en/events/{slug}
            # https://webook.com/en/experiences/{slug}
            # Avoid URLs ending in /book
            if "/book" in loc:
                continue
                
            match = re.search(r'/(events|experiences|restaurants|packages)/([^/?#]+)$', loc)
            if match:
                slugs.add(match.group(2))
        
        return slugs
    except Exception as e:
        logger.error(f"Failed to process {url}: {e}")
        return set()

async def sync_from_sitemap():
    logger.info("Starting Exhaustive Sitemap Discovery...")
    index_xml = await get_xml(SITEMAP_INDEX)
    root = ET.fromstring(index_xml)
    namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
    
    all_slugs = set()
    sitemaps = [s.find('ns:loc', namespace).text for s in root.findall('ns:sitemap', namespace)]
    
    # We only care about events, experiences, restaurants, packages
    target_sitemaps = [s for s in sitemaps if any(x in s for x in ["events", "experiences", "restaurants", "packages"])]
    
    logger.info(f"Found {len(target_sitemaps)} relevant sitemaps.")
    
    for s_url in target_sitemaps:
        slugs = await extract_slugs_from_sitemap(s_url)
        all_slugs.update(slugs)
    
    logger.info(f"TOTAL UNIQUE SLUGS EXTRACTED: {len(all_slugs)}")
    
    # Save to file for transparency
    with open("scratch/sitemap_slugs.txt", "w") as f:
        for s in sorted(all_slugs):
            f.write(f"{s}\n")
            
    # Now, insert them as shells in the DB
    async with AsyncSessionLocal() as db:
        # Get "Webook" genre as default for sitemap events
        stmt = select(Genre).where(Genre.slug == "webook")
        webook_genre = (await db.execute(stmt)).scalar_one_or_none()
        genre_id = webook_genre.id if webook_genre else None
        
        new_count = 0
        for slug in all_slugs:
            # Check if exists
            stmt = select(LiveEvent).where(LiveEvent.slug == slug)
            existing = (await db.execute(stmt)).scalar_one_or_none()
            
            if not existing:
                new_ev = LiveEvent(
                    slug=slug,
                    webook_id=f"shell_{slug}",
                    title_ar=slug, # Placeholder
                    title_en=slug, # Placeholder
                    status="UPCOMING",
                    genre_id=genre_id
                )
                db.add(new_ev)
                new_count += 1
                
        await db.commit()
        logger.info(f"SYNC COMPLETE: Inserted {new_count} new event shells.")

if __name__ == "__main__":
    asyncio.run(sync_from_sitemap())

