import asyncio
import json
import logging
import sys
import os
from datetime import datetime, timezone
from typing import Optional, Union, Dict, Any
from unittest.mock import MagicMock, AsyncMock

# Set up environment
os.environ["PYTHONPATH"] = "."
logging.basicConfig(level=logging.INFO)

# Mock classes that behave like Aiogram objects but are not frozen
class MockUser:
    def __init__(self, id, first_name):
        self.id = id
        self.first_name = first_name

class MockChat:
    def __init__(self, id):
        self.id = id

class MockMessage:
    def __init__(self, chat, from_user, bot):
        self.chat = chat
        self.from_user = from_user
        self.bot = bot
        self.message_id = 1
        self.text = "/start"
        self.answer = AsyncMock()
        self.edit_text = AsyncMock()

class MockCallbackQuery:
    def __init__(self, from_user, message, data):
        self.from_user = from_user
        self.message = message
        self.data = data
        self.id = "cb_1"
        self.answer = AsyncMock()

from apps.bot.handlers_v2.dashboard import handle_start
from apps.bot.handlers_v2.booking import handle_booking_start, handle_browse_org
from core.tracing.context import TraceContext

async def run_validation():
    print("\n" + "="*60)
    print("  FINAL PRODUCTION VALIDATION - RUNTIME SIMULATION")
    print("="*60)

    user_id = 12345
    chat_id = 67890
    
    user = MockUser(user_id, "Test")
    chat = MockChat(chat_id)
    bot = MagicMock()
    msg = MockMessage(chat, user, bot)
    
    # --- STEP 1: /start ---
    print("\n[STEP 1] Simulating /start...")
    from aiogram.fsm.context import FSMContext
    from aiogram.fsm.storage.memory import MemoryStorage
    from aiogram.types import User, Chat, Message
    
    # We still need real FSMContext but it doesn't need real Bot
    storage = MemoryStorage()
    state = FSMContext(storage, key=MagicMock()) 
    
    trace = TraceContext(trace_id="TEST-1", user_id=user_id, chat_id=chat_id)
    
    # We have to use the real handle_start which might use some aiogram-specific checks
    # Let's hope it only accesses .from_user.id and .chat.id
    try:
        await handle_start(msg, state, trace_ctx=trace)
    except Exception as e:
        print(f"  [ERROR] handle_start failed: {e}")
        import traceback
        traceback.print_exc()

    # Capture the markup sent to answer
    if msg.answer.called:
        args, kwargs = msg.answer.call_args
        text = args[0]
        markup = kwargs.get("reply_markup")
        print(f"  Outbound: answer")
        print(f"  Text: {text[:50]}...")
        if markup:
            btns = [b.text for row in markup.inline_keyboard for b in row]
            print(f"  Buttons: {btns}")
    
    # --- STEP 2: click 'booking_start' ---
    print("\n[STEP 2] Simulating click 'booking_start'...")
    cb = MockCallbackQuery(user, msg, "booking_start")
    
    await handle_booking_start(cb, state, trace_ctx=trace)
    
    if msg.edit_text.called:
        args, kwargs = msg.edit_text.call_args
        text = args[0]
        markup = kwargs.get("reply_markup")
        print(f"  Outbound: edit_text")
        if markup:
            btns = [b.text for row in markup.inline_keyboard for b in row]
            print(f"  Buttons found: {btns}")
            if any("\U0001f3ad" in b for b in btns):
                print("  [SUCCESS] Categories rendered with emojis!")
            else:
                print("  [FAIL] No categories in markup!")
        else:
            print("  [FAIL] No markup found!")

    # --- STEP 3: click a category ---
    if msg.edit_text.called:
        markup = msg.edit_text.call_args[1].get("reply_markup")
        cat_btn = next((b for row in markup.inline_keyboard for b in row if "browse_org:" in b.callback_data), None)
        if cat_btn:
            print(f"\n[STEP 3] Simulating click '{cat_btn.callback_data}'...")
            cb.data = cat_btn.callback_data
            msg.edit_text.reset_mock()
            await handle_browse_org(cb, state, trace_ctx=trace)
            
            if msg.edit_text.called:
                markup = msg.edit_text.call_args[1].get("reply_markup")
                btns = [b.text for row in markup.inline_keyboard for b in row]
                print(f"  Events found: {len([b for b in btns if '\U0001f4cc' in b])}")
                if any("\U0001f4cc" in b for b in btns):
                    print("  [SUCCESS] Event list rendered!")
                else:
                    print("  [FAIL] Event list empty!")

    print("\n" + "="*60)
    print("  VALIDATION COMPLETE")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(run_validation())
