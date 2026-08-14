import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import Message

async def main():
    print("Starting simple bot...")
    bot = Bot(token="8175406356:AAHQNdJt06FZbKt_wT9ioYUWvJgaEEaBiB0")
    dp = Dispatcher()
    
    @dp.message()
    async def echo(message: Message):
        await message.answer("I am alive!")
    
    print("Polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
