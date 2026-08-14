import asyncio
import sys
import os

# Add root folder to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/.."))

from core.database.postgres import AsyncSessionLocal
from database.models.account import AuthSession
from modules.webook.client import WebookApiClient

async def test_live_account():
    print("=" * 60)
    print("LIVE WEBOOK ACCOUNT & RESERVATION PIPELINE AUDIT")
    print("=" * 60)
    
    # 1. Fetch the registered user account
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        stmt = select(AuthSession).where(AuthSession.email == 'sypherdox@gmail.com')
        res = await db.execute(stmt)
        account = res.scalar_one_or_none()
        
    if not account:
        print("[-] FAILED: Account sypherdox@gmail.com not found in database!")
        return
        
    print(f"[+] Loaded registered account: {account.email}")
    print(f"    - Role: {account.role}")
    print(f"    - Health Status: {account.health}")
    print(f"    - Token Length: {len(account.bearer_token) if account.bearer_token else 0} chars")
    
    if not account.bearer_token:
        print("[-] FAILED: Bearer token is empty in the database!")
        return
        
    # 2. Initialize the dynamic client
    c = WebookApiClient(bearer_token=account.bearer_token)
    
    # 3. Test Profile Endpoint
    print("\n[STEP 1] Validating profile authentication...")
    try:
        profile = await c.get_me()
        print(f"[+] Profile API Call Successful!")
        print(f"    - Response Status: {profile.get('_http_status', 200)}")
        print(f"    - Response Keys: {list(profile.keys())}")
        if "data" in profile:
            user_data = profile["data"] or {}
            print(f"    - User Email: {user_data.get('email')}")
            print(f"    - User Name: {user_data.get('name') or user_data.get('first_name')}")
            print(f"    - User Active: {user_data.get('status') or 'N/A'}")
        else:
            print("    [-] Profile returned no 'data' wrapper.")
    except Exception as e:
        print(f"[-] Profile API failed: {e}")
        
    # 4. Fetch a working event to test tickets/holds
    test_slug = "songsofthemountains-7jun"
    print(f"\n[STEP 2] Fetching ticket packages for: {test_slug}")
    try:
        res_t = await c.get_event_tickets(test_slug)
        tickets = res_t.get("event_tickets") or []
        print(f"[+] Successfully fetched {len(tickets)} ticket packages.")
        for t in tickets[:2]:
            print(f"    - Package '{t.get('title')}' | Price: {t.get('price')} {t.get('currency')} | Original: {t.get('original_price')} | Available: {not t.get('sold_out')}")
    except Exception as e:
        print(f"[-] Tickets retrieval failed: {e}")
        
    print("\n" + "=" * 60)
    print("AUDIT COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_live_account())
