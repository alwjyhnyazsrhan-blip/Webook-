import asyncio
import aiohttp

async def send():
    token = "8175406356:AAHQNdJt06FZbKt_wT9ioYUWvJgaEEaBiB0"
    chat_id = 6943712474
    text = "\u26a0ï¸ DEVELOPER TEST: Please DO NOT use the bot for sensitive operations. Webook protection is our TOP priority. Bot is under final maintenance - announcement will come soon. /start to see status."
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as resp:
            data = await resp.json()
            print("Result:", data)

asyncio.run(send())
