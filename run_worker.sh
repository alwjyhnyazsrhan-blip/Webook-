#!/bin/bash
# Fix line endings for all Python files
find /app -name "*.py" -exec sed -i 's/\r$//' {} \;
# Run the worker
exec python -m apps.worker.main