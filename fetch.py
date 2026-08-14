import urllib.request
import json
req = urllib.request.Request('https://api.webook.com/api/v2/events/rsl-25-26-al-fateh-vs-al-najma-692735?lang=ar', headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36', 'Origin': 'https://webook.com', 'Referer': 'https://webook.com/'})
try:
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read())
        event = data.get('data', {})
        print('Event Tickets:', json.dumps(event.get('event_tickets', []), ensure_ascii=False)[:500])
        print('Seats IO:', json.dumps(event.get('seats_io', {}), ensure_ascii=False))
except Exception as e:
    print('Error:', e)
