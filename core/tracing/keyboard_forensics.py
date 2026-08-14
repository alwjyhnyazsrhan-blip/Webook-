from __future__ import annotations
from typing import List, Optional, Union
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from core.tracing.context import TraceContext
from core.tracing.structured_logger import tlog

def validate_keyboard(
    markup: Union[InlineKeyboardMarkup, any], 
    context_name: str, 
    trace_ctx: Optional[TraceContext] = None,
    expected_min: int = 1
) -> bool:
    """
    Analyzes an InlineKeyboardMarkup for common issues via TraceContext.
    """
    if trace_ctx:
        trace_ctx.keyboard_check(markup, context_name=context_name, expected_min=expected_min)
        # We can still check the button count for the return value
        info = trace_ctx._last_keyboard_info
        if info:
            return info["button_count"] >= expected_min

    # Fallback if no trace_ctx
    count = 0
    if hasattr(markup, "inline_keyboard"):
        for row in markup.inline_keyboard:
            count += len(row)
    return count >= expected_min
