# Kill existing Webook Sniper bot processes to resolve TelegramConflictError
Get-Process | Where-Object { $_.ProcessName -eq "python" -and ($_.CommandLine -like "*apps/bot/main.py*" -or $_.CommandLine -like "*main.py*") } | Stop-Process -Force
Write-Host "Bot processes terminated successfully." -ForegroundColor Green
