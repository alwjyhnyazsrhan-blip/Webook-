import asyncio
import os
import logging
from unittest.mock import MagicMock, AsyncMock
from aiogram import types, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

# Set up environment
os.environ["PYTHONPATH"] = "."
logging.basicConfig(level=logging.INFO)
from core.logging.logger import logger

from core.database.postgres import AsyncSessionLocal
from database.models.discovery import LiveEvent
from apps.bot.handlers_v2.event_detail import handle_event_detail
from core.tracing.context import TraceContext

async def validate_seatmap_ui():
    print("\n" + "="*60)
    print("  SEATMAP UI VALIDATION (REGRESSION TEST)")
    print("="*60)

    slug = "spl-week-34-al-hazem-vs-al-taawoun-3710"
    user_id = 12345
    chat_id = 67890
    
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        from sqlalchemy.orm import joinedload
        stmt = select(LiveEvent).where(LiveEvent.slug == slug).options(joinedload(LiveEvent.genre))
        event = (await db.execute(stmt)).scalar_one_or_none()
        if not event:
            print(f"  [FAIL] Event {slug} not found in DB!")
            return

    user = MagicMock(spec=types.User); user.id = user_id; user.first_name = "Test"
    chat = MagicMock(spec=types.Chat); chat.id = chat_id
    bot = MagicMock(spec=Bot)
    
    msg = MagicMock(spec=types.Message)
    msg.chat = chat
    msg.from_user = user
    msg.bot = bot
    msg.message_id = 1
    msg.answer = AsyncMock()
    msg.answer_photo = AsyncMock()
    msg.edit_text = AsyncMock()

    cb = MagicMock(spec=types.CallbackQuery)
    cb.from_user = user
    cb.message = msg
    cb.bot = bot
    cb.data = f"e_det:{event.id}"
    cb.id = "cb_1"
    cb.answer = AsyncMock()

    storage = MemoryStorage()
    state = FSMContext(storage, key=MagicMock())
    trace = TraceContext(trace_id="VALIDATE-UI", user_id=user_id, chat_id=chat_id)

    print(f"\n[STEP 1] Triggering handle_event_detail for {slug}...")
    await handle_event_detail(cb, state, trace_ctx=trace)

    # Check if answer_photo was called
    if msg.answer_photo.called:
        args, kwargs = msg.answer_photo.call_args
        photo = kwargs.get("photo")
        print(f"  [SUCCESS] answer_photo called!")
        if hasattr(photo, 'path') or isinstance(photo, types.FSInputFile):
            path = photo.path if hasattr(photo, 'path') else str(photo)
            print(f"  [SUCCESS] Photo is local file: {path}")
            if os.path.exists(path):
                print(f"  [SUCCESS] Rendered PNG file exists: {os.path.getsize(path)} bytes")
            else:
                print(f"  [FAIL] Rendered PNG file DOES NOT EXIST at {path}")
        else:
            print(f"  [FAIL] Photo is NOT local file (it is {type(photo)})")
    else:
        print("  [FAIL] answer_photo was NOT called!")

    print("\n" + "="*60)
    print("  VALIDATION COMPLETE")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(validate_seatmap_ui())
