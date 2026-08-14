import asyncio
import json
from modules.webook.client import WebookApiClient

async def check():
    c = WebookApiClient()
    # Al Hazem vs Al Taawoun
    data = await c.get_seatcloud_chart_data('66e63c10464382fb1f049832', '35e36087-5483-4f23-82a3-51b70e3d0882')
    print(f"KEYS: {list(data.keys())}")
    # Print sample of the content
    content = data.get("content", {})
    print(f"CONTENT_KEYS: {list(content.keys())}")
    areas = content.get("areas", [])
    print(f"AREAS_COUNT: {len(areas)}")
    if areas:
        print("DEBUG: Sample Area:")
        print(json.dumps(areas[0], indent=2))

if __name__ == "__main__":
    asyncio.run(check())
