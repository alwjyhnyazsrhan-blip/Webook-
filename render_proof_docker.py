import asyncio
import os
from services.seatmap.renderer import render_seatmap_png

async def render():
    slug = "spl-week-32-al-kholood-vs-al-okhdood-9720"
    chart_key = "aae06c55-8d5f-418c-812d-dc11452cb757"
    event_key = "rsl-25-26-al-kholood-vs-al-okhdood-1776346186"
    workspace_key = "66e63c10464382fb1f049832"
    
    print(f"Starting render for {slug}...")
    path = await render_seatmap_png(
        slug=slug,
        chart_key=chart_key,
        event_key=event_key,
        workspace_key=workspace_key
    )
    if path:
        print(f"SUCCESS|PATH:{path}|SIZE:{os.path.getsize(path)}")
    else:
        print("FAILED")

if __name__ == "__main__":
    asyncio.run(render())
