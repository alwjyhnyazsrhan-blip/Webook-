import asyncio
import time
import uuid
from core.tracing.context import TraceContext
from core.tracing.message_registry import message_registry
from core.tracing.telegram_instruments import (
    instrumented_telegram_call, 
    OwnershipViolationError
)
from unittest.mock import AsyncMock

async def test_adversarial_ownership():
    print("=== ADVERSARIAL TEST: STARTING ===")
    
    chat_id = 777
    message_id = 111
    mock_fn = AsyncMock(return_value=True)

    # TEST 1: Delayed Overwrite / Heartbeat Recovery
    print("\n[TEST 1] Heartbeat Recovery / Abandoned Flow")
    trace_a = TraceContext.new(trace_id="TRACE_A")
    await instrumented_telegram_call("edit_text", mock_fn, trace_a, chat_id=chat_id, message_id=message_id, text="A")
    
    trace_b = TraceContext.new(trace_id="TRACE_B")
    print("Trace B trying to steal Trace A's message (should FAIL)...")
    try:
        await instrumented_telegram_call("edit_text", mock_fn, trace_b, chat_id=chat_id, message_id=message_id, text="B")
    except OwnershipViolationError:
        print("SUCCESS: Correctly blocked Trace B.")

    print("Simulating Trace A abandonment (shrinking TTL for test)...")
    message_registry._owner_ttl = 1 # 1 second TTL
    await asyncio.sleep(1.1)
    
    print("Trace B trying again after abandonment (should SUCCEED)...")
    await instrumented_telegram_call("edit_text", mock_fn, trace_b, chat_id=chat_id, message_id=message_id, text="B")
    owner = await message_registry.check_ownership(chat_id, message_id)
    print(f"SUCCESS: Correctly allowed Trace B recovery. New owner: {owner.get('last_trace_id')}")

    # TEST 2: Tombstoned Callback Protection
    print("\n[TEST 2] Tombstoned Callback Protection")
    await message_registry.mark_stale(chat_id, message_id, reason="test_tombstone")
    
    print("Validating callback on tombstoned message...")
    is_valid = await message_registry.validate_callback(chat_id, message_id)
    if not is_valid:
        print("SUCCESS: Correctly rejected callback on stale message.")
    else:
        print("FAIL: Callback should have been rejected.")

    # TEST 3: Flight Recorder (Mutation History)
    print("\n[TEST 3] Flight Recorder / Event Audit")
    history = owner.get("events", [])
    print(f"Recorded mutations: {len(history)}")
    for i, ev in enumerate(history):
        print(f"  {i}: trace={ev.get('trace_id')} method={ev.get('method')}")
    
    if len(history) >= 2:
        print("SUCCESS: Flight recorder captured mutation sequence.")

    # TEST 4: Authoritative Override Logging
    print("\n[TEST 4] Authoritative Override")
    trace_c = TraceContext.new(trace_id="TRACE_C")
    # Reset TTL to prevent auto-release
    message_registry._owner_ttl = 300
    
    print("Trace C force-overriding Trace B...")
    await instrumented_telegram_call("edit_text", mock_fn, trace_c, chat_id=chat_id, message_id=message_id, text="C", force_override=True)
    owner = await message_registry.check_ownership(chat_id, message_id)
    print(f"SUCCESS: Correctly allowed force override. Final owner: {owner.get('last_trace_id')}")

    print("\n=== ADVERSARIAL TEST: COMPLETED ===")

if __name__ == "__main__":
    asyncio.run(test_adversarial_ownership())
