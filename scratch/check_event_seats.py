import asyncio
import sys
import os

# Add root folder to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/.."))

from modules.webook.client import WebookApiClient

async def check_seats():
    print("=" * 60)
    print("SEATCLOUD REAL-TIME INVENTORY AUDIT (AL-KHOLOOD VS AL-FATEH)")
    print("=" * 60)
    
    slug = "spl-week-34-al-kholood-vs-al-fateh-9190"
    client = WebookApiClient()
    
    # 1. SeatCloud Keys returned in details data
    workspace_key = "66e63c10464382fb1f049832"
    event_key = "rsl-25-26-al-kholood-vs-al-fateh-1778685751"
    
    print(f"[+] Using keys: workspace={workspace_key}, event={event_key}")
    
    # 2. Query real-time SeatCloud available chairs report
    print("\n[+] Calling SeatCloud live report API `/report/available`...")
    available_report = await client.get_seatcloud_report_available(
        workspace_key=workspace_key, event_key=event_key
    )
    
    if not available_report:
        print("\n[-] RESULT: Live report returned EMPTY (0 chairs available)!")
        print("    This confirms that the event is 100% SOLD OUT on SeatCloud!")
        return
        
    print(f"\n[+] SUCCESS: Found {len(available_report)} chairs in SeatCloud report!")
    
    # 3. Categorize remaining chairs
    categories = {}
    for chair in available_report:
        cat_key = chair.get("categoryKey") or "Unknown"
        cat_label = chair.get("categoryLabel") or "Unknown"
        key = f"{cat_label} (Key: {cat_key})"
        categories[key] = categories.get(key, 0) + 1
        
    print("\n[+] Available Seats by Category:")
    for cat, count in categories.items():
        print(f"    - {cat}: {count} seats available")
        
    print("\n" + "=" * 60)
    print("AUDIT COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(check_seats())
