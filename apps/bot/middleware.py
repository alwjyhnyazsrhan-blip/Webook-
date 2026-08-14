from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message
from core.config.settings import settings
from core.logging.logger import logger

class AdminMiddleware(BaseMiddleware):
    """
    Restricts access to bot commands based on ADMIN_IDS.
    """
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        if not isinstance(event, Message):
            return await handler(event, data)

        user_id = event.from_user.id
        if user_id not in settings.admin_ids:
            logger.warning("Unauthorized access attempt", user_id=user_id, command=event.text)
            await event.answer("\u26a0ï¸ Access Denied: You are not authorized to use this bot.")
            return

        return await handler(event, data)

class LoggingMiddleware(BaseMiddleware):
    """
    Logs every interaction for auditability.
    """
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        if isinstance(event, Message):
            logger.info("Bot interaction", user_id=event.from_user.id, text=event.text)
        
        return await handler(event, data)
