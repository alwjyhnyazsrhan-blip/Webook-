$env:PYTHONPATH = "."
$env:PYTHONIOENCODING = "utf-8"

# Start the Bot
Start-Process python -ArgumentList "apps/bot/main.py" -NoNewWindow -PassThru > bot.pid

# Start the Worker
Start-Process python -ArgumentList "services/reservation/worker.py" -NoNewWindow -PassThru > worker.pid

Write-Host "Services started."
