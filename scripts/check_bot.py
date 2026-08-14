import asyncio
from aiogram import Bot
from core.config.settings import settings

async def check_bot():
    bot = Bot(token="8175406356:AAHQNdJt06FZbKt_wT9ioYUWvJgaEEaBiB0")
    try:
        me = await bot.get_me()
        print(f"Bot is ALIVE: @{me.username}")
    except Exception as e:
        print(f"Bot failed to start: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(check_bot())
