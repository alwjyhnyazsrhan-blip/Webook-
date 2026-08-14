import asyncio
import uuid
from core.tracing.context import TraceContext
from core.tracing.message_registry import message_registry, init_registry
from core.tracing.telegram_instruments import (
    instrumented_telegram_call, 
    OwnershipViolationError
)
from redis.asyncio import Redis
from unittest.mock import AsyncMock

async def test_ownership():
    # Setup - use memory fallback implicitly by not calling init_registry
    
    chat_id = 999
    message_id = 888
    
    # 1. Trace A edits
    trace_a = TraceContext.new(trace_id="TRACE_A")
    mock_fn = AsyncMock(return_value=True)
    
    print("--- TRACE A editing ---")
    await instrumented_telegram_call(
        "edit_text", mock_fn, trace_a, 
        chat_id=chat_id, message_id=message_id, text="A content"
    )
    
    owner = await message_registry.check_ownership(chat_id, message_id)
    print(f"Current owner: {owner.get('last_trace_id')}")
    
    # 2. Trace B tries to edit
    trace_b = TraceContext.new(trace_id="TRACE_B")
    print("\n--- TRACE B editing (should be blocked) ---")
    try:
        await instrumented_telegram_call(
            "edit_text", mock_fn, trace_b, 
            chat_id=chat_id, message_id=message_id, text="B content"
        )
        print("FAIL: TRACE B was NOT blocked!")
    except OwnershipViolationError as e:
        print(f"SUCCESS: TRACE B was blocked: {e}")
        
    # 3. Trace B force edits
    print("\n--- TRACE B force editing (should succeed) ---")
    await instrumented_telegram_call(
        "edit_text", mock_fn, trace_b, 
        chat_id=chat_id, message_id=message_id, text="B force", 
        force_override=True
    )
    owner = await message_registry.check_ownership(chat_id, message_id)
    print(f"New owner: {owner.get('last_trace_id')}")
    
    # 4. Tombstoning test
    print("\n--- Tombstoning test ---")
    await message_registry.mark_stale(chat_id, message_id)
    print("Trying to edit stale message (Trace B)...")
    try:
        await instrumented_telegram_call(
            "edit_text", mock_fn, trace_b, 
            chat_id=chat_id, message_id=message_id, text="B stale"
        )
        print("FAIL: Stale message edit was NOT blocked!")
    except OwnershipViolationError:
        print("SUCCESS: Stale message edit was blocked.")

if __name__ == "__main__":
    asyncio.run(test_ownership())
