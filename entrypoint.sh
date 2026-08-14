#!/bin/bash
# Fix line endings for all Python files (Windows compatibility)
find /app -name "*.py" -type f -exec sed -i "s/\r$//" {} \; 2>/dev/null || true

# Execute the main command
exec "$@"