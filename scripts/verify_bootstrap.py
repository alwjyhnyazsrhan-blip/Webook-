import asyncio
from unittest.mock import MagicMock, AsyncMock
from apps.api.main import app
from apps.bot.main import dp, bot
from core.logging.logger import setup_logging, logger
import uvicorn

async def verify_bootstrap():
    setup_logging()
    logger.info("Starting Bootstrap Verification...")

    # Mock bot to avoid network calls
    bot.get_me = AsyncMock(return_value=MagicMock(username="WebookSniperBot"))
    
    # Mock uvicorn server to run briefly
    config = uvicorn.Config(app, host="127.0.0.1", port=8000, log_level="error")
    server = uvicorn.Server(config)

    # Start API and Bot
    logger.info("Booting API and Bot services...")
    
    # We run the server and the bot polling
    # For verification, we just start them and then cancel after 3 seconds
    api_task = asyncio.create_task(server.serve())
    bot_task = asyncio.create_task(dp.start_polling(bot))

    await asyncio.sleep(3)
    
    logger.info("Verification period complete. Initiating graceful shutdown...")
    
    # Trigger Shutdown
    server.should_exit = True
    await dp.stop_polling()
    
    await asyncio.gather(api_task, bot_task, return_exceptions=True)
    logger.info("Bootstrap Verification SUCCESS.")

if __name__ == "__main__":
    asyncio.run(verify_bootstrap())
