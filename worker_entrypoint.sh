#!/bin/bash
# Fix all Python files line endings before starting
if [ -d /app ]; then
    find /app -name "*.py" -exec sed -i -e 's/\r$//' -e 's/\xEF\xBB\xBF//' {} \; 2>/dev/null || true
fi

# Run the worker
exec python -m apps.worker.main