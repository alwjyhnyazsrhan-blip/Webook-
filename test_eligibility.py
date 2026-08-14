import asyncio
import httpx
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.webook.client import WebookApiClient

async def test_token_eligibility():
    # Use a token from the DB
    import sqlite3
    conn = sqlite3.connect('data/webook.db')
    cur = conn.cursor()
    cur.execute("SELECT bearer_token, proxy_url FROM auth_sessions WHERE health='ACTIVE' LIMIT 1")
    row = cur.fetchone()
    conn.close()
    
    if not row:
        print("No active accounts found.")
        return
        
    token, proxy = row
    print(f"Testing token: {token[:10]}...")
    
    client = WebookApiClient(bearer_token=token, proxy=proxy)
    
    # Target event
    event_slug = "spl-week-34-al-hazem-vs-al-taawoun-3710"
    
    # 1. Fetch event detail
    detail = await client.get_event_detail(event_slug)
    if not detail:
        print("Failed to fetch event detail.")
        return
    
    event_id = detail.get("id") or detail.get("_id")
    print(f"Event ID: {event_id}")
    
    # 2. Check eligibility (if endpoint exists)
    # Actually, we'll try a dummy checkout_best_available
    try:
        res = await client.checkout_best_available(event_slug, event_id, [{"ticket_type_id": "dummy", "quantity": 1}])
        print(f"Checkout Result: {res}")
    except Exception as e:
        print(f"Error during checkout: {e}")

if __name__ == "__main__":
    asyncio.run(test_token_eligibility())
