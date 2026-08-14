import asyncio
import os
from services.seatmap.renderer import _try_pillow_render
from pathlib import Path

async def test_pillow():
    slug = "spl-week-32-al-kholood-vs-al-okhdood-9720"
    workspace_key = "66e63c10464382fb1f049832"
    chart_key = "aae06c55-8d5f-418c-812d-dc11452cb757"
    output_path = Path("/app/data/pillow_test.png")
    
    print(f"Starting Pillow render for {slug}...")
    success = await _try_pillow_render(
        slug=slug,
        workspace_key=workspace_key,
        chart_key=chart_key,
        output_path=output_path
    )
    if success:
        print(f"SUCCESS|PATH:{output_path}|SIZE:{os.path.getsize(output_path)}")
    else:
        print("FAILED")

if __name__ == "__main__":
    asyncio.run(test_pillow())
