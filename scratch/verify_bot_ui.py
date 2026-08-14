import asyncio
import os
import sys
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Update, Message, CallbackQuery, User, Chat

# Fix for Windows Arabic printing
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

os.environ["PYTHONPATH"] = "."
from apps.bot.handlers_v2.router import get_router
from core.tracing.middleware import TracingMiddleware

# Capture list for bot calls
CAPTURED_CALLS = []

async def simulate_bot():
    print("\n" + "="*60)
    print("  BOT UI INTERACTION SIMULATION")
    print("="*60)

    # 1. Setup Mock Bot and Dispatcher
    bot = AsyncMock(spec=Bot)
    bot.token = "123456789:ABCDEF"
    
    # Custom mocks to capture text/markup
    async def mock_send_message(*args, **kwargs):
        CAPTURED_CALLS.append(("SEND_MESSAGE", kwargs))
        return MagicMock(spec=Message)

    async def mock_edit_message_text(*args, **kwargs):
        CAPTURED_CALLS.append(("EDIT_TEXT", kwargs))
        return MagicMock(spec=Message)

    bot.send_message = mock_send_message
    bot.edit_message_text = mock_edit_message_text
    bot.answer_callback_query = AsyncMock(return_value=True)

    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    dp.update.outer_middleware(TracingMiddleware())
    dp.include_router(get_router())

    user = User(id=12345, is_bot=False, first_name="Test", last_name="User", username="testuser")
    chat = Chat(id=12345, type="private")
    now = datetime.now(timezone.utc)

    async def run_test(update: Update, label: str):
        print(f"\n[TEST] {label}")
        CAPTURED_CALLS.clear()
        await dp.feed_update(bot, update)
        
        if not CAPTURED_CALLS:
            print("  (No response captured)")
        for rtype, kwargs in CAPTURED_CALLS:
            txt = kwargs.get('text', '')
            print(f"  {rtype}: {txt[:200]}...")
            if "reply_markup" in kwargs:
                markup = kwargs["reply_markup"]
                buttons = []
                for row in markup.inline_keyboard:
                    buttons.extend([b.text for b in row])
                print(f"    Buttons: {buttons}")

    # â•â•â• TEST 1: /start â•â•â•
    start_msg = Message(message_id=1, date=now, chat=chat, from_user=user, text="/start")
    await run_test(Update(update_id=1, message=start_msg), "Sending /start")

    # â•â•â• TEST 2: Click 'Booking Start' â•â•â•
    cb = CallbackQuery(id="1", from_user=user, chat_instance="1", message=start_msg, data="booking_start")
    await run_test(Update(update_id=2, callback_query=cb), "Clicking 'New Reservation'")

    # â•â•â• TEST 3: Browse Category 'Football' â•â•â•
    cb = CallbackQuery(id="2", from_user=user, chat_instance="1", message=start_msg, data="browse_org:saudi-pro-league")
    await run_test(Update(update_id=3, callback_query=cb), "Browsing Saudi Pro League")

    print("\n" + "="*60)
    print("  SIMULATION COMPLETE")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(simulate_bot())
