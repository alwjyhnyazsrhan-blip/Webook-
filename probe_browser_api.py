import asyncio, httpx, re, json

async def explore():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'token': 'e9aac1f2f0b6c07d6be070ed14829de684264278359148d6a582ca65a50934d2',
    }
    async with httpx.AsyncClient(headers=headers, timeout=15, follow_redirects=True) as client:
        # Try fetching the events SSR page
        r = await client.get('https://webook.com/ar/events?visible_in=webook')
        print(f'events page: {r.status_code}')

        # Look for JSON data in the page
        patterns = [
            r'window\.__NEXT_DATA__\s*=\s*(\{[^<]{1,20000})',
            r'"events":\s*\[',
            r'"data":\s*\{[^}]{100,}',
        ]
        for p in patterns:
            matches = re.findall(p, r.text)
            if matches:
                print(f'Pattern {p[:30]}... found {len(matches)} matches')
                if len(matches[0]) > 500:
                    print(f'  Sample: {matches[0][:300]}')

        # Try the API routes used by Next.js SSR
        routes = [
            'https://api.webook.com/api/v2/organizations/rsl/events?lang=ar&per_page=50',
            'https://api.webook.com/api/v2/organizations/riyadh-season/events?lang=ar&per_page=50',
            'https://api.webook.com/api/v2/organizations/mdl-beast/events?lang=ar&per_page=50',
            # Try with different visible_in params
            'https://api.webook.com/api/v2/organizations/webook/events?lang=ar&per_page=50&visible_in=webook',
            'https://api.webook.com/api/v2/organizations/riyadh-season/events?lang=ar&per_page=50&visible_in=webook',
        ]
        for url in routes:
            try:
                r = await client.get(url)
                if r.status_code != 404:
                    data = r.json()
                    events = (data.get('data') or data).get('data', [])
                    print(f'[{r.status_code}] {url} | events={len(events)}')
            except Exception as e:
                print(f'ERR {url}: {e}')

asyncio.run(explore())
