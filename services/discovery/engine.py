# services/discovery/engine.py
"""
Webook Event Discovery Engine
"""
import os
import sys
from pathlib import Path

_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

class DiscoveryEngine:
    def __init__(self):
        self.cached_events = []

    async def sync_all(self):
        print("[DISCOVERY] Syncing latest Webook events catalog...")
        return {"synced": True, "count": len(self.cached_events)}

    async def get_all_events(self, limit=10):
        return self.cached_events[:limit]
