from utils.queue_watchdog import QueueWatchdog
﻿import re
import os

def instrument_worker(filepath):
    print(f"Instrumenting {filepath}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Add Tracing Imports
    if "core.tracing" not in content:
        import_marker = "from core.logging.logger import logger"
        tracing_imports = (
            "\nfrom core.tracing.worker_tracer import traced_worker_task\n"
        )
        content = content.replace(import_marker, import_marker + tracing_imports)

    # 2. Decorate _execute_task
    if "@traced_worker_task" not in content:
        content = content.replace("async def _execute_task(self, task_id: int):", "@traced_worker_task\n    async def _execute_task(self, task_id: int):")

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Done.")

if __name__ == "__main__":
    instrument_worker(r"services\reservation\worker.py")


# Queue stale protection patch
def evaluate_queue_health(queue_watchdog, logger=None):
    state = queue_watchdog.recommendation()

    if logger:
        logger.warning(f"[QUEUE_HEALTH] {state}")

    return state
