print("1. Starting script")
import sys
sys.stdout.flush()

try:
    print("2. Importing modules")
    import asyncio
    print("3. Imported asyncio")
    import httpx
    print("4. Imported httpx")
    
    print("5. Running async test")
    async def test():
        print("6. Inside async")
        headers = {
            "Accept": "application/json",
            "Origin": "https://webook.com",
            "Referer": "https://webook.com/",
            "token": "e9aac1f2f0b6c07d6be070ed14829de684264278359148d6a582ca65a50934d2"
        }
        
        print("7. Making request")
        async with httpx.AsyncClient(headers=headers, timeout=15) as client:
            print("8. Requesting events")
            r = await client.get("https://api.webook.com/api/v2/organizations/riyadh-season/events?lang=ar&status=upcoming&page=1&per_page=5")
            print(f"9. Status: {r.status_code}")
            
            if r.status_code == 200:
                data = r.json()
                print(f"10. Data keys: {list(data.keys())}")
                events = data.get("data", {}).get("data", [])
                print(f"11. Events: {len(events)}")
                
                for ev in events[:3]:
                    print(f"  - {ev.get('title')} | {ev.get('slug')}")
            else:
                print(f"Error: {r.text[:300]}")
        
    print("12. Running test")
    asyncio.run(test())
    print("13. Done")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    
print("14. Script finished")
