from __future__ import annotations
import json
import logging
from typing import Any, Optional, Union, List
from aiogram import Bot
from aiogram.types import Message, InlineKeyboardMarkup, CallbackQuery
from core.tracing.context import TraceContext
from core.tracing.structured_logger import tlog

logger = logging.getLogger("webook_forensics")

class OwnershipViolationError(Exception):
    """Raised when a mutation is rejected due to ownership boundaries."""
    pass

def validate_payload_strict(text: str, reply_markup: Optional[Any], context: str):
    """
    STRICT Assertions on the Telegram payload before sending.
    Raises ValueError if constraints are violated.
    """
    if not reply_markup:
        return

    markup = reply_markup
    if hasattr(reply_markup, "as_markup"):
        markup = reply_markup.as_markup()
    
    if not isinstance(markup, InlineKeyboardMarkup):
        return

    rows = markup.inline_keyboard
    if not rows:
        raise ValueError(f"[{context}] STRICT_ASSERT_FAILED: inline_keyboard is empty")

    total_buttons = 0
    for i, row in enumerate(rows):
        if not row:
            raise ValueError(f"[{context}] STRICT_ASSERT_FAILED: row {i} is empty")
        for j, btn in enumerate(row):
            total_buttons += 1
            cb_data = getattr(btn, "callback_data", None)
            url = getattr(btn, "url", None)
            
            if not cb_data and not url:
                raise ValueError(f"[{context}] STRICT_ASSERT_FAILED: button at row {i} col {j} has no callback_data or url")
            
            if cb_data:
                cb_len = len(cb_data.encode("utf-8"))
                if cb_len > 64:
                    raise ValueError(f"[{context}] STRICT_ASSERT_FAILED: callback_data too long ({cb_len} bytes) for button '{btn.text}'")

    if total_buttons == 0:
         raise ValueError(f"[{context}] STRICT_ASSERT_FAILED: total_buttons is 0")

def get_serialized_markup(reply_markup: Optional[Any]) -> Optional[str]:
    if not reply_markup:
        return None
    try:
        markup = reply_markup
        if hasattr(reply_markup, "as_markup"):
            markup = reply_markup.as_markup()
        
        if hasattr(markup, "model_dump"):
            return json.dumps(markup.model_dump(), ensure_ascii=False)
        elif hasattr(markup, "dict"):
            return json.dumps(markup.dict(), ensure_ascii=False)
        else:
            return str(markup)
    except Exception as e:
        return f"SERIALIZATION_ERROR: {e}"

async def instrumented_telegram_call(
    method_name: str,
    call_fn,
    trace_ctx: Optional[TraceContext],
    force_override: bool = False,
    **kwargs
) -> Any:
    trace_id = trace_ctx.trace_id if trace_ctx else "no_trace"
    text = kwargs.get("text") or kwargs.get("caption") or ""
    reply_markup = kwargs.get("reply_markup")
    chat_id = kwargs.get("chat_id") or "unknown"
    message_id = kwargs.get("message_id") or "unknown"

    from core.tracing.message_registry import message_registry
    
    # 0. ENFORCE OWNERSHIP
    if chat_id != "unknown" and message_id != "unknown":
        if force_override:
            owner_info = await message_registry.check_ownership(chat_id, message_id)
            if owner_info and owner_info.get("last_trace_id") != trace_id:
                logger.critical(
                    f"[REGISTRY_OVERRIDE] Authoritative override detected!\n"
                    f"chat={chat_id} msg={message_id}\n"
                    f"New Trace: {trace_id}\n"
                    f"PREVIOUS Owner: {owner_info.get('last_trace_id')}\n"
                    f"Method: {method_name}"
                )
        
        is_allowed = await message_registry.validate_mutation(
            chat_id=chat_id, 
            message_id=message_id, 
            trace_id=trace_id if trace_ctx else None,
            force=force_override
        )
        if not is_allowed:
            owner_info = await message_registry.check_ownership(chat_id, message_id)
            err_msg = (
                f"[OWNERSHIP_BLOCK] Mutation rejected! chat={chat_id} msg={message_id}\n"
                f"Attempted by: {trace_id}\n"
                f"Owned by: {owner_info.get('last_trace_id') if owner_info else 'unknown'}\n"
                f"Is Stale: {owner_info.get('is_stale') if owner_info else 'no'}"
            )
            logger.error(err_msg)
            if trace_ctx:
                trace_ctx.stage("ownership_blocked", owner=owner_info.get('last_trace_id') if owner_info else 'unknown')
            raise OwnershipViolationError(err_msg)

    # 1. Capture and Validate
    validate_payload_strict(text, reply_markup, method_name)
    serialized_markup = get_serialized_markup(reply_markup)
    button_count = 0
    if reply_markup:
        m = reply_markup.as_markup() if hasattr(reply_markup, "as_markup") else reply_markup
        if hasattr(m, "inline_keyboard"):
            button_count = sum(len(row) for row in m.inline_keyboard)

    # 2. LOG [TELEGRAM_OUTBOUND]
    log_msg = (
        f"[TELEGRAM_OUTBOUND]\n"
        f"trace_id={trace_id}\n"
        f"method={method_name}\n"
        f"chat_id={chat_id}\n"
        f"message_id={message_id}\n"
        f"text_preview={str(text)[:50]}...\n"
        f"has_reply_markup={bool(reply_markup)}\n"
        f"button_count={button_count}\n"
        f"serialized_markup={serialized_markup}"
    )
    logger.info(log_msg)
    if trace_ctx:
        trace_ctx.stage("telegram_outbound", method=method_name, button_count=button_count)

    # 3. EXECUTE
    try:
        result = await call_fn(**kwargs)
        
        # 4. Record mutation in registry if successful
        if chat_id != "unknown":
            final_message_id = message_id
            if isinstance(result, Message):
                final_message_id = result.message_id
            
            if final_message_id != "unknown":
                await message_registry.register_mutation(
                    chat_id=chat_id,
                    message_id=final_message_id,
                    trace_id=trace_id,
                    payload={"reply_markup": reply_markup, "text": text, "method": method_name}
                )

        # 5. LOG [TELEGRAM_RESPONSE]
        res_json = "{}"
        try:
            if hasattr(result, "model_dump"):
                res_json = json.dumps(result.model_dump(), ensure_ascii=False)
            elif hasattr(result, "dict"):
                res_json = json.dumps(result.dict(), ensure_ascii=False)
            else:
                res_json = str(result)
        except:
            res_json = str(result)

        logger.info(f"[TELEGRAM_RESPONSE] ok=true trace_id={trace_id} result={res_json}")
        if trace_ctx:
            trace_ctx.stage("telegram_ok", method=method_name)
        return result

    except Exception as e:
        logger.error(f"[TELEGRAM_RESPONSE] ok=false trace_id={trace_id} error={str(e)}")
        if trace_ctx:
            trace_ctx.snapshot(e, handler=method_name)
        raise

# Helper functions
async def traced_send_message(bot: Bot, chat_id: Union[int, str], text: str, trace_ctx: Optional[TraceContext] = None, **kwargs) -> Message:
    return await instrumented_telegram_call("send_message", bot.send_message, trace_ctx, chat_id=chat_id, text=text, **kwargs)

async def traced_edit_text(bot: Bot, chat_id: Union[int, str], message_id: int, text: str, trace_ctx: Optional[TraceContext] = None, force_override: bool = False, **kwargs) -> Union[Message, bool]:
    return await instrumented_telegram_call("edit_message_text", bot.edit_message_text, trace_ctx, force_override=force_override, chat_id=chat_id, message_id=message_id, text=text, **kwargs)

async def traced_answer_callback(callback: CallbackQuery, text: Optional[str] = None, trace_ctx: Optional[TraceContext] = None, **kwargs):
    return await instrumented_telegram_call("answer_callback", callback.answer, trace_ctx, text=text, **kwargs)

async def traced_message_edit(message: Message, text: str, trace_ctx: Optional[TraceContext] = None, force_override: bool = False, **kwargs) -> Union[Message, bool]:
    return await instrumented_telegram_call("message_edit_text", message.edit_text, trace_ctx, force_override=force_override, text=text, **kwargs)

async def traced_message_answer(message: Message, text: str, trace_ctx: Optional[TraceContext] = None, **kwargs) -> Message:
    return await instrumented_telegram_call("message_answer", message.answer, trace_ctx, text=text, **kwargs)

async def traced_callback_edit(callback: CallbackQuery, text: str, trace_ctx: Optional[TraceContext] = None, force_override: bool = False, **kwargs) -> Union[Message, bool]:
    return await instrumented_telegram_call("callback_edit_text", callback.message.edit_text, trace_ctx, force_override=force_override, text=text, **kwargs)

async def traced_answer_photo(message: Message, photo: Any, caption: Optional[str] = None, trace_ctx: Optional[TraceContext] = None, **kwargs) -> Message:
    return await instrumented_telegram_call("answer_photo", message.answer_photo, trace_ctx, photo=photo, caption=caption, **kwargs)

async def traced_edit_reply_markup(bot: Bot, chat_id: Union[int, str], message_id: int, reply_markup: Optional[InlineKeyboardMarkup] = None, trace_ctx: Optional[TraceContext] = None, force_override: bool = False, **kwargs) -> Union[Message, bool]:
    return await instrumented_telegram_call("edit_message_reply_markup", bot.edit_message_reply_markup, trace_ctx, force_override=force_override, chat_id=chat_id, message_id=message_id, reply_markup=reply_markup, **kwargs)
