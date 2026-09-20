# core/logging/logger.py
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

class AppLogger:
    def __init__(self, name="webook"):
        self._logger = logging.getLogger(name)

    def info(self, msg, **kwargs):
        extra_str = f" | {kwargs}" if kwargs else ""
        self._logger.info(f"{msg}{extra_str}")

    def warning(self, msg, **kwargs):
        extra_str = f" | {kwargs}" if kwargs else ""
        self._logger.warning(f"{msg}{extra_str}")

    def error(self, msg, **kwargs):
        extra_str = f" | {kwargs}" if kwargs else ""
        self._logger.error(f"{msg}{extra_str}")

    def debug(self, msg, **kwargs):
        extra_str = f" | {kwargs}" if kwargs else ""
        self._logger.debug(f"{msg}{extra_str}")

logger = AppLogger()
