# Clean start script for Webook Sniper Bot
./maintenance/kill_bot.ps1
Write-Host "Starting Webook Sniper Bot..." -ForegroundColor Cyan
python -u apps/bot/main.py
