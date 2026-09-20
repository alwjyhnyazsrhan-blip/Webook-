# apps/worker/main.py
"""
Reservation Worker Background Service
"""
import os
import sys
import asyncio
from pathlib import Path

_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

async def main():
    print("[WORKER] Reservation Worker started.")
    while True:
        try:
            await asyncio.sleep(60)
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"[WORKER ERROR] {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
