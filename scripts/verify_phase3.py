import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from aiogram import types
from apps.bot.middleware import AdminMiddleware
from apps.bot.handlers import handle_reserve
from core.config.settings import settings
from core.logging.logger import setup_logging, logger

async def verify_bot_foundation():
    setup_logging()
    logger.info("Verifying Phase 3: Bot Foundation and Middleware...")

    # 1. Test Admin Middleware
    middleware = AdminMiddleware()
    
    # Mock Event (Message) from Unauthorized User
    mock_message = AsyncMock(spec=types.Message)
    mock_message.from_user = MagicMock(id=999999) # Not in settings.admin_ids
    mock_message.text = "/reserve test 1"
    mock_message.answer = AsyncMock()
    
    mock_handler = AsyncMock()
    
    logger.info("Testing Admin Middleware with unauthorized user...")
    await middleware(mock_handler, mock_message, {})
    
    mock_message.answer.assert_called_with("âš ¸ Access Denied: You are not authorized to use this bot.")
    mock_handler.assert_not_called()
    logger.info("Admin blocking verified.")

    # 2. Test Handler -> Orchestrator Integration
    # Mock Message from Authorized User
    authorized_msg = AsyncMock(spec=types.Message)
    authorized_msg.from_user = MagicMock(id=123456789) # In settings.admin_ids
    authorized_msg.reply = AsyncMock()
    
    # Mock Command Object
    from aiogram.filters.command import CommandObject
    mock_command = MagicMock(spec=CommandObject)
    mock_command.args = "test-slug 2"

    with patch('services.reservation.orchestrator.ReservationOrchestrator.start_reservation') as mock_start:
        mock_start.return_value = MagicMock(id=101, status=MagicMock(value="PENDING"))
        
        logger.info("Testing handle_reserve integration...")
        await handle_reserve(authorized_msg, mock_command)
        
        mock_start.assert_called_once_with(123456789, "test-slug", 2)
        authorized_msg.reply.assert_called()
        logger.info("Handler -> Orchestrator integration verified.")

    logger.info("Phase 3: Bot Foundation Verification SUCCESS.")

if __name__ == "__main__":
    asyncio.run(verify_bot_foundation())
