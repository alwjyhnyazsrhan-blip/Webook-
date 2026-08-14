import asyncio
import httpx
import xml.etree.ElementTree as ET

async def list_all_sitemaps():
    url = "https://webook.com/sitemap.xml"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=30)
        root = ET.fromstring(resp.text)
        ns = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        smaps = [s.find('ns:loc', ns).text for s in root.findall('ns:sitemap', ns)]
        for s in smaps:
            print(s)

if __name__ == "__main__":
    asyncio.run(list_all_sitemaps())
