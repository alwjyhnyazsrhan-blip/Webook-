import json
import logging
from datetime import datetime, timezone

class StructuredLogger:
    """
    Production-Grade Logger.
    Outputs JSON logs for automated tracing and observability.
    """
    def __init__(self, name: str):
        import os
        self.logger = logging.getLogger(name)
        level_str = os.getenv("LOG_LEVEL", "INFO").upper()
        level = getattr(logging, level_str, logging.INFO)
        self.logger.setLevel(level)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            self.logger.addHandler(handler)

    def info(self, event: str, **kwargs):
        self._log("INFO", event, **kwargs)

    def warning(self, event: str, **kwargs):
        self._log("WARNING", event, **kwargs)

    def error(self, event: str, **kwargs):
        self._log("ERROR", event, **kwargs)

    def critical(self, event: str, **kwargs):
        self._log("CRITICAL", event, **kwargs)

    def warning(self, event: str, **kwargs):
        self._log("WARNING", event, **kwargs)

    def debug(self, event: str, **kwargs):
        self._log("DEBUG", event, **kwargs)

    def _log(self, level: str, event: str, **kwargs):
        log_payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "event": event,
            **kwargs
        }
        # In production, we print as JSON for ELK/CloudWatch parsing
        print(json.dumps(log_payload, ensure_ascii=False))

logger = StructuredLogger("webook_sniper")
