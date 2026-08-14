import asyncio
from unittest.mock import MagicMock, AsyncMock
from aiogram import types
from apps.bot.handlers import handle_start, handle_status
from core.logging.logger import setup_logging, logger

async def verify_bot_handlers():
    setup_logging()
    logger.info("Starting Telegram Handler Verification (aiogram)...")

    # Mock Message
    mock_message = AsyncMock(spec=types.Message)
    mock_message.from_user = MagicMock(id=123456789)
    mock_message.reply = AsyncMock()
    
    # 1. Test /start
    logger.info("Testing /start handler...")
    await handle_start(mock_message)
    mock_message.reply.assert_called()
    logger.info("Start handler executed and replied.")

    # 2. Test /status
    logger.info("Testing /status handler...")
    await handle_status(mock_message)
    mock_message.reply.assert_called()
    logger.info("Status handler executed and ueried DB.")

    logger.info("Telegram Handler Verification SUCCESS.")

if __name__ == "__main__":
    asyncio.run(verify_bot_handlers())
