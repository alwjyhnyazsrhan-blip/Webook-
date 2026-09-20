# services/monitor/ghost.py
GHOST_SCAN_INTERVAL = 30

class GhostMonitor:
    def __init__(self, db_session=None):
        self.db = db_session

    async def scan_once(self):
        pass
