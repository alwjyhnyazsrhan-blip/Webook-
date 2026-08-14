import asyncio
import json
from modules.webook.client import WebookApiClient

async def main():
    c = WebookApiClient()
    res = await c.get_event_detail('rsl-25-26-al-fateh-vs-al-najma-692735')
    print('TICKETS:', json.dumps(res.get('event_tickets', []), ensure_ascii=False, indent=2))
    print('PACKAGES:', json.dumps(res.get('ticket_packages', []), ensure_ascii=False, indent=2))
    print('ZONES:', json.dumps(res.get('zones', []), ensure_ascii=False, indent=2))
    print('SEATS:', json.dumps(res.get('seats_io', {}), ensure_ascii=False, indent=2))
    
asyncio.run(main())
