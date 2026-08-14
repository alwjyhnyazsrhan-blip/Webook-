
import time
from datetime import datetime, timedelta

QUEUE_STALE_SECONDS = 900
QUEUE_HARD_TIMEOUT = 2700

class QueueWatchdog:
    def __init__(self):
        self.started = time.time()
        self.last_progress = time.time()
        self.last_position = None

    def update(self, position=None):
        if position != self.last_position:
            self.last_progress = time.time()
            self.last_position = position

    def is_stale(self):
        return (time.time() - self.last_progress) > QUEUE_STALE_SECONDS

    def is_dead(self):
        return (time.time() - self.started) > QUEUE_HARD_TIMEOUT

    def recommendation(self):
        if self.is_dead():
            return "RESTART_SESSION"
        if self.is_stale():
            return "REFRESH_QUEUE"
        return "HEALTHY"
