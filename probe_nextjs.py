import asyncio, httpx, re, json

async def explore_browser_endpoints():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
    }
    async with httpx.AsyncClient(headers=headers, timeout=15, follow_redirects=True) as client:
        # Get the main page and look for API calls in the JS bundles
        r = await client.get('https://webook.com/ar')
        html = r.text

        # Find Next.js data bundles
        next_data = re.findall(r'<script id="__NEXT_DATA__"[^>]*>([^<]+)</script>', html)
        for nd in next_data:
            try:
                data = json.loads(nd)
                print(f'NEXT_DATA keys: {list(data.keys())}')
                # Look for event-related data
                payload = data.get('props', {}).get('pageProps', {}) or data.get('props', {}) or {}
                print(f'pageProps keys: {list(payload.keys())}')
                for k, v in payload.items():
                    if isinstance(v, (list, dict)):
                        print(f'  {k}: type={type(v).__name__} len={len(v) if hasattr(v, "__len__") else "N/A"}')
                        if isinstance(v, list) and len(v) > 0:
                            print(f'    first item keys: {list(v[0].keys()) if isinstance(v[0], dict) else v[0]}')
                        if isinstance(v, dict):
                            print(f'    keys: {list(v.keys())[:15]}')
            except Exception as e:
                print(f'PARSE_ERROR: {e}')

        # Also check the homepage JS for event endpoints
        js_urls = re.findall(r'src="(/_[next|webpack][^"]+\.js)"', html)
        print(f'\nJS bundles found: {len(js_urls)}')

asyncio.run(explore_browser_endpoints())
