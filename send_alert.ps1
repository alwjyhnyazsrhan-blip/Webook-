[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$body = @{
    chat_id = 6943712474
    text = [System.Text.Encoding]::UTF8.GetString([System.Text.Encoding]::GetEncoding("ISO-8859-1").GetBytes("🔒 <b>DEVELOPER TEST MESSAGE:</b>"))
    parse_mode = "HTML"
}
$body.text = "🔒 DEVELOPER TEST MESSAGE: Please do NOT use the bot for sensitive operations right now. Webook protection is our top priority. Bot is under final maintenance - announcement coming soon."

$json = $body | ConvertTo-Json -Compress
$uri = "https://api.telegram.org/bot8175406356:AAHQNdJt06FZbKt_wT9ioYUWvJgaEEaBiB0/sendMessage"

try {
    $resp = Invoke-RestMethod -Uri $uri -Method Post -ContentType "application/json; charset=utf-8" -Body ([System.Text.Encoding]::UTF8.GetBytes($json))
    Write-Output "Message sent OK: $($resp.result.message_id)"
} catch {
    Write-Output "Error: $($_.Exception.Message)"
}