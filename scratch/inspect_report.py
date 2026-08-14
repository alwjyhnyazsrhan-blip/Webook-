import asyncio
import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/.."))

from modules.webook.client import WebookApiClient

async def main():
    api = WebookApiClient()
    workspace_key = "66e63c10464382fb1f049832"
    event_key = "rsl-25-26-al-kholood-vs-al-fateh-1778685751"
    print(f"Fetching SeatCloud available report for workspace={workspace_key} event={event_key}...")
    try:
        report = await api.get_seatcloud_report_available(workspace_key, event_key)
        print(f"Success! Total seats in report: {len(report)}")
        if report:
            print("First 3 seat objects in report:")
            print(json.dumps(report[:3], indent=2, ensure_ascii=False))
            
            # Count seats per categoryKey and categoryLabel
            stats = {}
            for seat in report:
                ck = seat.get("categoryKey") or seat.get("category_key")
                cl = seat.get("categoryLabel") or seat.get("category_label")
                key = f"Key: {ck} | Label: {cl}"
                stats[key] = stats.get(key, 0) + 1
            print("\nSeats count per category key/label in report:")
            for k, v in stats.items():
                print(f" - {k}: {v} seats")
    except Exception as e:
        print(f"Fetch failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
