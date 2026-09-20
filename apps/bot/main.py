# apps/bot/main.py
"""
Bot Runner Module
"""
import os
import sys
import asyncio
from pathlib import Path

# Ensure root is in sys.path
_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

async def start_bot():
    """Starts the background bot runner loop"""
    print("[BOT] Bot engine initialized successfully.")
    while True:
        try:
            await asyncio.sleep(60)
        except asyncio.CancelledError:
            print("[BOT] Bot loop shutting down.")
            break
        except Exception as e:
            print(f"[BOT ERROR] {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(start_bot())
