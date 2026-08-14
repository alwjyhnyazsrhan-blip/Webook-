import asyncio
import aiohttp

async def main():
    token = "8175406356:AAHQNdJt06FZbKt_wT9ioYUWvJgaEEaBiB0"
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": 6943712474,
        "text": "\u26a0ï¸ DEVELOPER TEST: Please DO NOT use the bot for sensitive operations. Webook protection is TOP priority. Bot is under final maintenance - announcement will come soon. /start to see status.",
        "parse_mode": "HTML"
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as resp:
            result = await resp.json()
            print("Sent:", result)

if __name__ == "__main__":
    asyncio.run(main())
