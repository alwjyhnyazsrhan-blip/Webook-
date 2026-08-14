import asyncio
import json
import httpx
import sys
import os

# Add the project root to sys.path
sys.path.append(os.getcwd())

from modules.webook.client import WebookApiClient

async def main():
    client = WebookApiClient()
    slug = "rsl-25-26-al-ahli-vs-al-kholood-05162026"
    try:
        resp = await client.get_event_detail(slug)
        print("FULL EVENT DETAIL DATA:")
        print(json.dumps(resp, indent=2))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
