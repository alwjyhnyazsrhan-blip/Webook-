import sys
import asyncio

async def main():
    print("Starting test...", flush=True)
    sys.stdout.flush()
    try:
        print("Importing DB...", flush=True)
        from core.database.postgres import AsyncSessionLocal
        print("DB imported", flush=True)
        
        print("Importing Discovery...", flush=True)
        from services.discovery.engine import DiscoveryEngine
        print("Discovery imported", flush=True)
        
        print("Creating Discovery...", flush=True)
        discovery = DiscoveryEngine()
        print("Discovery created", flush=True)
        
        print("Getting events...", flush=True)
        events = await discovery.get_all_events(limit=5)
        print(f"Got {len(events)} events", flush=True)
        
        for e in events:
            print(f"  - {e.slug}", flush=True)
            
    except Exception as e:
        print(f"ERROR: {e}", flush=True)
        import traceback
        traceback.print_exc()

asyncio.run(main())
