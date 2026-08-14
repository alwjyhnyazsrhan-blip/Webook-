from __future__ import annotations
import logging
from typing import Any, Optional, Union
from aiogram import types
from core.tracing.telegram_instruments import (
    traced_callback_edit, 
    traced_message_edit, 
    traced_message_answer, 
    traced_answer_photo,
    traced_answer_callback,
    traced_edit_reply_markup
)
from core.tracing.context import TraceContext
from core.tracing.message_registry import message_registry

logger = logging.getLogger("webook_ui")

async def edit_or_reply(
    event: Union[types.Message, types.CallbackQuery],
    text: str,
    reply_markup: Optional[Any] = None,
    parse_mode: str = "HTML",
    image_url: Optional[str] = None,
    trace_ctx: Optional[TraceContext] = None,
    force_new: bool = False
):
    """
    Authoritative UI delivery.
    Decides whether to edit the current message or send a new one.
    Implements message tombstoning (marking old messages as stale).
    """
    chat_id = event.message.chat.id if isinstance(event, types.CallbackQuery) else event.chat.id
    message_id = event.message.message_id if isinstance(event, types.CallbackQuery) else event.message_id

    if image_url:
        # Photos cannot be edited from text messages, and vice versa in some cases.
        # We generally prefer to send a new message for photos.
        if isinstance(event, types.CallbackQuery):
            # Tombstone the old message
            await message_registry.mark_stale(chat_id, message_id)
            try:
                # Clear the old keyboard to prevent orphan clicks
                await traced_edit_reply_markup(event.bot, chat_id, message_id, reply_markup=None, trace_ctx=trace_ctx, force_override=True)
            except: pass
            
            await traced_answer_photo(
                event.message, 
                photo=image_url, 
                caption=text, 
                parse_mode=parse_mode, 
                reply_markup=reply_markup,
                trace_ctx=trace_ctx
            )
            try:
                await event.message.delete()
            except: pass
            return
        else:
            await traced_answer_photo(
                event, 
                photo=image_url, 
                caption=text, 
                parse_mode=parse_mode, 
                reply_markup=reply_markup,
                trace_ctx=trace_ctx
            )
            return

    # Text-only flow
    if isinstance(event, types.CallbackQuery) and not force_new:
        try:
            await traced_callback_edit(
                event, 
                text=text, 
                parse_mode=parse_mode, 
                reply_markup=reply_markup,
                trace_ctx=trace_ctx
            )
        except Exception as e:
            if "message is not modified" in str(e).lower():
                pass
            else:
                logger.warning(f"[UI_EDIT_FAIL] {e}, falling back to new message")
                # Tombstone old message
                await message_registry.mark_stale(chat_id, message_id)
                try:
                    await traced_edit_reply_markup(event.bot, chat_id, message_id, reply_markup=None, trace_ctx=trace_ctx, force_override=True)
                except: pass

                await traced_message_answer(
                    event.message, 
                    text=text, 
                    parse_mode=parse_mode, 
                    reply_markup=reply_markup,
                    trace_ctx=trace_ctx
                )
    else:
        target = event.message if isinstance(event, types.CallbackQuery) else event
        await traced_message_answer(
            target, 
            text=text, 
            parse_mode=parse_mode, 
            reply_markup=reply_markup,
            trace_ctx=trace_ctx
        )

async def notify(callback: types.CallbackQuery, text: str, alert: bool = False, trace_ctx: Optional[TraceContext] = None):
    await traced_answer_callback(callback, text=text, show_alert=alert, trace_ctx=trace_ctx)
