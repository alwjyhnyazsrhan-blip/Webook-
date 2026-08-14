import asyncio
from apps.bot.main import start_bot
from core.logging.logger import logger

async def main():
    logger.info("Starting ONLY the bot for testing...")
    await start_bot()

if __name__ == "__main__":
    asyncio.run(main())
