import asyncio
import os
import json
import sys

# Fix for Windows Arabic printing
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

os.environ["PYTHONPATH"] = "."
from modules.webook.client import WebookApiClient
from modules.session.context import create_session_context, close_session_context

async def test_hold_token():
    slug = "spl-week-32-al-kholood-vs-al-okhdood-9720"
    
    # We use a mock account but real client
    ctx = await create_session_context(
        account_id="hold_test",
        event_slug=slug,
        flow_type="seated",
        proxy_config=None,
        fingerprint_headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Origin": "https://webook.com",
            "Referer": "https://webook.com/ar",
        }
    )
    
    client = WebookApiClient(session_ctx=ctx)
    
    print(f"\n[STEP 1] Requesting hold_token for {slug}...")
    # Many Webook events allow hold_token without Bearer (it's the 'session start')
    # Or they return a 422 with Turnstile
    res = await client.hold_token(slug)
    
    print(f"\n[HOLD_TOKEN_RESULT]")
    print(f"HTTP Status: {res.get('_http_status')}")
    print(f"Body: {json.dumps(res, indent=2, ensure_ascii=False)[:1000]}")
    
    if res.get('_http_status') == 200:
        print("\n[SUCCESS] Provider accepted the basic hold request!")
    elif res.get('_http_status') == 422:
        print("\n[SUCCESS] Provider reached! (Blocked by Turnstile, as expected for guest)")
    else:
        print("\n[FAIL] Provider rejected the request (likely 401 or 403)")

    await close_session_context(ctx)

if __name__ == "__main__":
    asyncio.run(test_hold_token())
