import asyncio
import httpx
import re
import xml.etree.ElementTree as ET
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SitemapCheck")

async def get_xml(url: str):
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=30)
        return resp.text

async def check_sitemaps():
    index_xml = await get_xml("https://webook.com/sitemap.xml")
    root = ET.fromstring(index_xml)
    namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
    
    sitemaps = [s.find('ns:loc', namespace).text for s in root.findall('ns:sitemap', namespace)]
    target_sitemaps = [s for s in sitemaps if any(x in s for x in ["events", "experiences", "restaurants", "packages"])]
    
    total_uniue = set()
    for s_url in target_sitemaps:
        xml = await get_xml(s_url)
        s_root = ET.fromstring(xml)
        slugs = set()
        for url_tag in s_root.findall('ns:url', namespace):
            loc = url_tag.find('ns:loc', namespace).text
            if "/book" in loc: continue
            match = re.search(r'/(events|experiences|restaurants|packages)/([^/?#]+)$', loc)
            if match:
                slugs.add(match.group(2))
        logger.info(f"Sitemap {s_url}: Found {len(slugs)} unique slugs")
        total_uniue.update(slugs)
    
    logger.info(f"FINAL TOTAL UNIQUE SLUGS: {len(total_uniue)}")

if __name__ == "__main__":
    asyncio.run(check_sitemaps())
