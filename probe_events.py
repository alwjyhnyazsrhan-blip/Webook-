import asyncio, httpx

async def sample_events():
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'token': 'e9aac1f2f0b6c07d6be070ed14829de684264278359148d6a582ca65a50934d2',
        'Accept': 'application/json, text/plain, */*',
    }
    async with httpx.AsyncClient(headers=headers, timeout=15, follow_redirects=True) as client:
        slugs = [
            'comedy-night-show-697812',
            'mdlbeast-beast-house-ec',
            'fit-expo-tickets-948503',
            'reignited-2-rs24-tickets-141864',
            'one-mic-comedy-shows-tickets-873299',
            'improv-night-show-274410',
        ]
        for slug in slugs:
            r = await client.get(f'https://api.webook.com/api/v2/events/{slug}?lang=ar')
            if r.status_code == 200:
                data = r.json()
                inner = data.get('data', {})
                event_type = inner.get('type') or ''
                category = inner.get('category') or ''
                is_seated = inner.get('is_seated') or False
                is_experience = inner.get('is_experience') or False
                is_show = inner.get('is_show') or False
                venue = inner.get('venue_name') or ''
                print(f'{slug} | type={event_type} cat={category} seated={is_seated} exp={is_experience} show={is_show} venue={venue}')
            else:
                print(f'{slug}: {r.status_code}')

asyncio.run(sample_events())
