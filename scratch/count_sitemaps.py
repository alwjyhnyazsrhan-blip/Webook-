import asyncio
import httpx
import xml.etree.ElementTree as ET

async def run():
    ns = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
    async with httpx.AsyncClient() as client:
        r = await client.get('https://webook.com/sitemap.xml')
        root = ET.fromstring(r.text)
        smaps = [s.find('ns:loc', ns).text for s in root.findall('ns:sitemap', ns)]
        total_urls = 0
        for smap in smaps:
            try:
                r2 = await client.get(smap)
                root2 = ET.fromstring(r2.text)
                count = len(root2.findall('ns:url', ns))
                print(f"{smap}: {count}")
                total_urls += count
            except:
                print(f"{smap}: FAILED")
        print(f"TOTAL URLS ACROSS ALL SITEMAPS: {total_urls}")

if __name__ == "__main__":
    asyncio.run(run())
