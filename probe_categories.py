import asyncio, httpx

async def find_categories():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128',
        'token': 'e9aac1f2f0b6c07d6be070ed14829de684264278359148d6a582ca65a50934d2',
        'Accept': 'application/json, text/plain, */*',
        'Origin': 'https://webook.com',
        'Referer': 'https://webook.com/ar',
    }
    async with httpx.AsyncClient(headers=headers, timeout=15, follow_redirects=True) as client:
        endpoints = [
            'https://api.webook.com/api/v2/categories?lang=ar&visible_in=webook',
            'https://api.webook.com/api/v2/category/all?lang=ar',
            'https://api.webook.com/api/v2/ticket-categories?lang=ar',
            'https://api.webook.com/api/v2/interests?lang=ar',
            'https://api.webook.com/api/v2/event-categories?lang=ar',
            'https://api.webook.com/api/v2/organizations?lang=ar&visible_in=webook',
            'https://api.webook.com/api/v2/organizations/list?lang=ar&visible_in=webook',
            'https://api.webook.com/api/v2/event-group?lang=ar',
            'https://api.webook.com/api/v2/event-groups?lang=ar&visible_in=webook',
            'https://api.webook.com/api/v2/experiences?lang=ar&visible_in=webook',
            'https://api.webook.com/api/v2/explore/home?lang=ar&visible_in=webook',
            'https://api.webook.com/api/v2/page/events?lang=ar',
        ]
        for url in endpoints:
            try:
                r = await client.get(url)
                body = r.text[:400]
                print(f'[{r.status_code}] {url}')
                if r.status_code == 200:
                    print(f'  BODY: {body}')
            except Exception as e:
                print(f'[ERR] {url} | {e}')

asyncio.run(find_categories())
