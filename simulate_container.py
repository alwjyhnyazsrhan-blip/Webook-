
import asyncio
import sys
import os
from unittest.mock import AsyncMock

# Add project root to sys.path
sys.path.append(os.getcwd())

from apps.bot.handlers import handle_view_chart

async def simulate_live_click(slug):
    mock_callback = AsyncMock()
    # handle_view_chart splits data at ":" and resolves slug
    # v_ch:SLUG or v_ch:ID
    # My resolver works with both.
    mock_callback.data = f"v_ch:{slug}"
    mock_callback.message = AsyncMock()
    mock_callback.message.answer_photo = AsyncMock()
    mock_callback.message.edit_text = AsyncMock()
    mock_callback.answer = AsyncMock()
    
    print(f"--- SIMULATING CLICK FOR: {slug} ---")
    await handle_view_chart(mock_callback)
    print(f"Simulation finished for {slug}")

if __name__ == "__main__":
    slugs = [
        "rsl-25-26-neom-vs-al-shabab-11052026",
        "the-wonder-jungle",
        "pubg-rs-24"
    ]
    for s in slugs:
        asyncio.run(simulate_live_click(s))
