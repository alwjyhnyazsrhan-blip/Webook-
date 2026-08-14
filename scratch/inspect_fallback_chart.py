import asyncio
import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/.."))

from modules.webook.client import WebookApiClient

async def main():
    api = WebookApiClient()
    workspace_key = "66e63c10464382fb1f049832"
    chart_key = "3b058c51-fee8-4864-a1e1-60444fc74246"
    print(f"Fetching SeatCloud chart data for workspace={workspace_key} chart_key={chart_key}...")
    try:
        chart = await api.get_seatcloud_chart_data(workspace_key, chart_key)
        print("Success! Keys in chart:")
        print(list(chart.keys()))
        content = chart.get("content") or {}
        print("Keys in content:")
        print(list(content.keys()))
        chairs = content.get("chairs") or []
        print(f"Total chairs in layout: {len(chairs)}")
        if chairs:
            print("First chair in layout:")
            print(json.dumps(chairs[0], indent=2, ensure_ascii=False))
            
            # Count specifications
            stats = {}
            for chair in chairs:
                spec = chair.get("specification", {})
                key = spec.get("key")
                stats[key] = stats.get(key, 0) + 1
            print("\nChairs count per specification key in layout:")
            for k, v in stats.items():
                print(f" - Specification Key {k}: {v} chairs")
    except Exception as e:
        print(f"Fetch failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
