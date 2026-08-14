from typing import Dict
from datetime import datetime

class DiscoveryMetricsStore:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DiscoveryMetricsStore, cls).__new__(cls)
            cls._instance.metrics = {
                "total_discovered": 0,
                "persisted": 0,
                "hydrated": 0,
                "categorized": 0,
                "uncategorized": 0,
                "403_failed": 0,
                "duplicate_skipped": 0,
                "last_sync_at": None
            }
        return cls._instance

    def update(self, new_metrics: Dict):
        for k, v in new_metrics.items():
            if k in self.metrics:
                self.metrics[k] += v
        self.metrics["last_sync_at"] = datetime.now().isoformat()

    def get_metrics(self) -> Dict:
        return self.metrics

    def reset(self):
        for k in self.metrics:
            if k != "last_sync_at":
                self.metrics[k] = 0

discovery_metrics = DiscoveryMetricsStore()
