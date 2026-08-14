import asyncio, httpx, re, json

async def bulk_classify():
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'token': 'e9aac1f2f0b6c07d6be070ed14829de684264278359148d6a582ca65a50934d2',
        'Accept': 'application/json, text/plain, */*',
    }
    async with httpx.AsyncClient(headers=headers, timeout=20, follow_redirects=True) as client:
        # Collect all sitemap slugs
        all_slugs = []
        for page_num in range(1, 5):
            r = await client.get(f'https://webook.com/sitemap_events_{page_num}.xml')
            locs = re.findall(r'<loc>https://webook\.com/en/events/([^/]+)</loc>', r.text)
            # Also find Arabic variants
            locs2 = re.findall(r'<loc>https://webook\.com/ar/events/([^/]+)</loc>', r.text)
            all_slugs.extend([l.split('/')[0].split('?')[0] for l in locs + locs2])
        all_slugs = list(set(all_slugs))
        print(f'Total unique slugs from sitemap: {len(all_slugs)}')

        # Sample 40 events to classify type distribution
        sample = all_slugs[:40]
        type_map = {}
        for slug in sample:
            try:
                r = await client.get(f'https://api.webook.com/api/v2/events/{slug}?lang=ar')
                if r.status_code == 200:
                    inner = r.json().get('data', {})
                    t = inner.get('type') or 'unknown'
                    cat = inner.get('category') or ''
                    is_exp = inner.get('is_experience') or False
                    is_show = inner.get('is_show') or False
                    is_seated = inner.get('is_seated') or False
                    venue = inner.get('venue_name') or ''
                    key = f'{t}|{cat}|exp={is_exp}|show={is_show}|seated={is_seated}|{venue[:20]}'
                    if key not in type_map:
                        type_map[key] = []
                    type_map[key].append(slug)
            except:
                pass
        for k, v in type_map.items():
            print(f'{k}: {len(v)} slugs - {v[:3]}')
        print(f'\nTotal types: {len(type_map)}')

asyncio.run(bulk_classify())
