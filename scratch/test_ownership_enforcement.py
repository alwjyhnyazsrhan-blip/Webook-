import asyncio
import os
import logging
from unittest.mock import MagicMock, AsyncMock
from aiogram import types, Bot

# Set up environment
os.environ["PYTHONPATH"] = "."
logging.basicConfig(level=logging.INFO)
from core.logging.logger import logger

from core.tracing.message_registry import message_registry
from core.tracing.telegram_instruments import traced_message_edit, traced_message_answer
from core.tracing.context import TraceContext

async def test_ownership():
    print("\n" + "="*60)
    print("  MESSAGE OWNERSHIP ENFORCEMENT VALIDATION")
    print("="*60)

    cid = 67890
    mid = 42
    trace_1 = TraceContext(trace_id="OWNER-1", user_id=123)
    trace_2 = TraceContext(trace_id="INVADER-1", user_id=123)

    # Manual Mock objects
    class MockChat: 
        def __init__(self, id): self.id = id
    class MockMessage:
        def __init__(self, chat, mid):
            self.chat = chat
            self.message_id = mid
            self.edit_text = AsyncMock(return_value=True)

    msg = MockMessage(MockChat(cid), mid)

    print("\n[STEP 1] Registering message 42 to trace OWNER-1...")
    await message_registry.register_mutation(cid, mid, trace_1.trace_id, {"text": "Initial"})

    # 2. Try to edit with SAME trace (should succeed)
    print("\n[STEP 2] Attempting edit with same trace (OWNER-1)...")
    try:
        await traced_message_edit(msg, "New Text", trace_ctx=trace_1)
        print("  [SUCCESS] Edit allowed.")
    except Exception as e:
        print(f"  [FAIL] Edit rejected unexpectedly: {e}")

    # 3. Try to edit with DIFFERENT trace
    print("\n[STEP 3] Attempting edit with DIFFERENT trace (INVADER-1)...")
    try:
        await traced_message_edit(msg, "Invader Text", trace_ctx=trace_2)
        print("  [FAIL] Edit allowed with different trace!")
    except Exception as e:
        print(f"  [SUCCESS] Edit REJECTED as expected: {e}")

    # 4. Tombstone check
    print("\n[STEP 4] Marking message 42 as STALE...")
    await message_registry.mark_stale(cid, mid)
    
    print("\n[STEP 5] Attempting edit on STALE message...")
    try:
        await traced_message_edit(msg, "Stale Text", trace_ctx=trace_1)
        print("  [FAIL] Edit allowed on stale message!")
    except Exception as e:
        print(f"  [SUCCESS] Edit REJECTED on stale message: {e}")

    print("\n" + "="*60)
    print("  VALIDATION COMPLETE")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(test_ownership())
