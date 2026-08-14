from __future__ import annotations
from typing import Any, Awaitable, Callable, Dict, Optional
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update
from core.tracing.buffer import new_trace, push_trace
from core.tracing.structured_logger import tlog

class TracingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # We only trace Updates that have a user/chat context
        user_id = None
        chat_id = None
        callback_data = None
        
        if isinstance(event, Update):
            if event.message:
                user_id = event.message.from_user.id
                chat_id = event.message.chat.id
            elif event.callback_query:
                user_id = event.callback_query.from_user.id
                chat_id = event.callback_query.message.chat.id if event.callback_query.message else None
                callback_data = event.callback_query.data

        # Create trace context
        ctx = new_trace(
            user_id=user_id,
            chat_id=chat_id,
            callback_data=callback_data
        )
        
        # Attach to data so handlers can access it
        data["trace_ctx"] = ctx
        
        if callback_data:
            from core.tracing.message_registry import message_registry
            msg_id = event.callback_query.message.message_id if event.callback_query.message else None
            if chat_id and msg_id:
                is_valid = await message_registry.validate_callback(chat_id, msg_id)
                if not is_valid:
                    tlog.callback_rejected(ctx, reason="stale_message")
                    try:
                        await event.callback_query.answer("\u26a0ï¸ \u0647\u0630\u0647 \u0627\u0644\u0631\u0633\u0627\u0644\u0629 \u0644\u0645 \u062a\u0639\u062f \u0635\u0627\u0644\u062d\u0629. \u064a\u0631\u062c\u0649 \u0627\u0633\u062a\u062e\u062f\u0627\u0645 \u0623\u062d\u062f\u062b \u0631\u0633\u0627\u0644\u0629.", show_alert=True)
                    except: pass
                    await push_trace(ctx)
                    return
            tlog.callback_received(ctx, callback_data=callback_data)

        try:
            result = await handler(event, data)
            return result
        except Exception as e:
            tlog.exception(ctx, handler=str(handler), exc=e)
            raise
        finally:
            await push_trace(ctx)

import functools

def traced_handler(func: Callable):
    @functools.wraps(func)
    async def wrapper(event: Any, state: Any = None, **kwargs):
        # The middleware should have put trace_ctx in kwargs if it's a handler call
        ctx = kwargs.get("trace_ctx")
        handler_name = func.__name__
        
        if ctx:
            tlog.handler_entered(ctx, handler=handler_name)
        
        try:
            if state:
                res = await func(event, state, **kwargs)
            else:
                res = await func(event, **kwargs)
            
            if ctx:
                tlog.handler_completed(ctx, handler=handler_name)
            return res
        except Exception as e:
            if ctx:
                tlog.handler_failed(ctx, handler=handler_name, exc=e)
            raise
    return wrapper
