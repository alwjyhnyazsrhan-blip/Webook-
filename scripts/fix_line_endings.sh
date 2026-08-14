#!/bin/bash
# Fix line endings
sed -i 's/\r$//' /app/services/reservation/worker.py
sed -i 's/\r$//' /app/modules/webook/client.py
sed -i 's/\r$//' /app/apps/bot/handlers.py

# Now run the main command
exec python -m apps.worker.main