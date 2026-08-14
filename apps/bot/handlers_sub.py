from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from core.database.postgres import AsyncSessionLocal
from database.repositories.user_prefs import UserPrefsRepository
from database.models.discovery import LiveEvent
from database.models.user_prefs import UserEventSubscription
from apps.bot.handlers import SniperStates, handle_start, safe_send_media, clean_html
from services.seat.manager import SeatManager
import logging

logger = logging.getLogger(__name__)
seat_manager = SeatManager()

async def handle_list_custom_events(callback: types.CallbackQuery):
    """List of Subscribed Events"""
    logger.info(f"[UX_TRACE] Listing custom events for user_id={callback.from_user.id}")
    async with AsyncSessionLocal() as db:
        repo = UserPrefsRepository(db)
        subs = await repo.get_user_subscriptions(callback.from_user.id)
        
        builder = InlineKeyboardBuilder()
        if not subs:
            text = "\u26a0ï¸ <b>\u0644\u0627 \u062a\u0648\u062c\u062f \u0641\u0639\u0627\u0644\u064a\u0627\u062a \u0645\u062e\u0635\u0635\u0629 \u062d\u0627\u0644\u064a\u0627\u064b.</b>"
        else:
            text = f"\U0001f4cb <b>\u0642\u0627\u0626\u0645\u0629 \u0627\u0644\u0641\u0639\u0627\u0644\u064a\u0627\u062a \u0627\u0644\u062a\u064a \u0637\u0644\u0628\u062a \u062a\u0646\u0628\u064a\u0647\u0627\u062a \u062e\u0627\u0635\u0629 \u0644\u0647\u0627:</b>\n"
            for sub in subs:
                event_name = clean_html(sub.event.title_ar if sub.event else f"Event {sub.event_id}")
                builder.row(types.InlineKeyboardButton(text=event_name, callback_data=f"s_det:{sub.event_id}"))
        
        builder.row(types.InlineKeyboardButton(text="\U0001f519 \u0639\u0648\u062f\u0629", callback_data="custom_events_menu"))
        await safe_send_media(callback, text, builder.as_markup())
    await callback.answer()

async def handle_sub_detail(callback: types.CallbackQuery):
    """Individual Event Subscription Detail & Management"""
    event_id = callback.data.split(":")[1]
    logger.info(f"[UX_TRACE] View Sub Detail for event_id={event_id}")
    
    async with AsyncSessionLocal() as db:
        repo = UserPrefsRepository(db)
        sub = await repo.get_subscription(callback.from_user.id, event_id)
        
        if not sub:
            stmt = select(LiveEvent).where(LiveEvent.id == event_id)
            event = (await db.execute(stmt)).scalar_one_or_none()
            if not event:
                await callback.answer("\u274c \u0627\u0644\u0641\u0639\u0627\u0644\u064a\u0629 \u063a\u064a\u0631 \u0645\u0648\u062c\u0648\u062f\u0629.", show_alert=True)
                return
            
            text = f"\U0001f514 <b>{clean_html(event.title_ar)}</b>\n\u0623\u0646\u062a \u063a\u064a\u0631 \u0645\u0634\u062a\u0631\u0643 \u0641\u064a \u062a\u0646\u0628\u064a\u0647\u0627\u062a \u0647\u0630\u0647 \u0627\u0644\u0641\u0639\u0627\u0644\u064a\u0629."
            builder = InlineKeyboardBuilder()
            builder.row(types.InlineKeyboardButton(text="\u2795 \u0625\u0636\u0627\u0641\u0629 \u0644\u0644\u0641\u0639\u0627\u0644\u064a\u0627\u062a \u0627\u0644\u0645\u062e\u0635\u0635\u0629", callback_data=f"s_add:{event_id}"))
            builder.row(types.InlineKeyboardButton(text="\U0001f519 \u0639\u0648\u062f\u0629", callback_data="list_custom_events"))
            await safe_send_media(callback, text, builder.as_markup())
            return

        event = sub.event
        def t(val): return "\u2705" if val else "\u274c"
        
        date_label = event.starts_at.strftime('%Y-%m-%d') if event.starts_at else '\u0642\u0631\u064a\u0628\u0627\u064b'
        detail_text = (
            f"\U0001f3ad <b>\u0625\u0639\u062f\u0627\u062f\u0627\u062a \u0627\u0644\u062a\u0646\u0628\u064a\u0647:</b>\n"
            f"â” â” â” â” â” â” â” â” â” â” â” â” â” â” \n"
            f"\U0001f3ab \u0627\u0644\u0641\u0639\u0627\u0644\u064a\u0629: {clean_html(event.title_ar)}\n"
            f"\U0001f4c5 \u0627\u0644\u062a\u0627\u0631\u064a\u062e: {date_label}\n\n"
            f"{t(sub.track_updates)} \u062a\u062a\u0628\u0639 \u062a\u062d\u062f\u064a\u062b\u0627\u062a \u0627\u0644\u0641\u0639\u0627\u0644\u064a\u0629\n"
            f"{t(sub.track_tickets)} \u062a\u062a\u0628\u0639 \u062a\u0648\u0641\u0631 \u0627\u0644\u062a\u0630\u0627\u0643\u0631\n"
            f"{t(sub.receive_notifications)} \u062a\u0644\u0642\u064a \u0627\u0644\u0625\u0634\u0639\u0627\u0631\u0627\u062a\n"
            f"â ° \u0627\u0644\u062a\u0630\u0643\u064a\u0631 \u0642\u0628\u0644 {sub.reminder_time_hours} \u0633\u0627\u0639\u0629\n\n"
            f"\u0627\u062e\u062a\u0631 \u0625\u062d\u062f\u0649 \u0627\u0644\u062e\u064a\u0627\u0631\u0627\u062a:"
        )

        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="ðŸª‘ \u062d\u062c\u0632 \u0627\u0644\u0645\u0642\u0627\u0639\u062f", callback_data=f"exec_b:{event.slug}"))
        builder.row(types.InlineKeyboardButton(text="\U0001f48e \u0639\u0631\u0636 \u0627\u0644\u0645\u062e\u0637\u0637", callback_data=f"s_map:{event.id}"))
        builder.row(types.InlineKeyboardButton(text="\U0001f515 \u0625\u064a\u0642\u0627\u0641 \u0627\u0644\u0625\u0634\u0639\u0627\u0631\u0627\u062a" if sub.receive_notifications else "\U0001f514 \u062a\u0641\u0639\u064a\u0644 \u0627\u0644\u0625\u0634\u0639\u0627\u0631\u0627\u062a", callback_data=f"s_tog:{event.id}:receive_notifications"))
        builder.row(types.InlineKeyboardButton(text=f"{t(sub.track_updates)} \u062a\u062a\u0628\u0639 \u0627\u0644\u062a\u062d\u062f\u064a\u062b\u0627\u062a", callback_data=f"s_tog:{event.id}:track_updates"))
        builder.row(types.InlineKeyboardButton(text=f"{t(sub.track_tickets)} \u062a\u062a\u0628\u0639 \u0627\u0644\u062a\u0630\u0627\u0643\u0631", callback_data=f"s_tog:{event_id}:track_tickets"))
        builder.row(types.InlineKeyboardButton(text="â° \u062a\u063a\u064a\u064a\u0631 \u0648\u0642\u062a \u0627\u0644\u062a\u0630\u0643\u064a\u0631", callback_data=f"p_rem:{event.id}"))
        builder.row(types.InlineKeyboardButton(text="\u274c \u062d\u0630\u0641 \u0627\u0644\u062a\u0646\u0628\u064a\u0647 \u0627\u0644\u0645\u062e\u0635\u0635", callback_data=f"s_del:{event.id}"))
        builder.row(types.InlineKeyboardButton(text="\U0001f519 \u0639\u0648\u062f\u0629", callback_data="list_custom_events"))

        await safe_send_media(callback, detail_text, builder.as_markup())
    await callback.answer()

async def handle_sub_toggle(callback: types.CallbackQuery):
    _, event_id, field = callback.data.split(":")
    async with AsyncSessionLocal() as db:
        repo = UserPrefsRepository(db)
        sub = await repo.get_subscription(callback.from_user.id, event_id)
        if sub:
            current_val = getattr(sub, field)
            setattr(sub, field, not current_val)
            await db.commit()
    await handle_sub_detail(callback)

async def handle_sub_map(callback: types.CallbackQuery):
    """Generate and send ACTUAL seat map report"""
    event_id = callback.data.split(":")[1]
    builder_load = InlineKeyboardBuilder()
    builder_load.row(types.InlineKeyboardButton(text="\U0001f519 \u0625\u0644\u063a\u0627\u0621", callback_data=f"s_det:{event_id}"))
    await safe_send_media(callback, "\U0001f3a8 <b>\u062c\u0627\u0631\u064a \u062c\u0644\u0628 \u0628\u064a\u0627\u0646\u0627\u062a \u0627\u0644\u0645\u062e\u0637\u0637 \u0648\u0627\u0644\u062a\u0648\u0641\u0631 \u0628\u062f\u0642\u0629 \u0639\u0627\u0644\u064a\u0629...</b>", builder_load.as_markup())
    
    report = await seat_manager.get_actual_map_summary(event_id)
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="\U0001f519 \u0639\u0648\u062f\u0629", callback_data=f"s_det:{event_id}"))
    
    # Report from seat_manager is assumed to be clean or pre-formatted
    await safe_send_media(callback, report, builder.as_markup())
    await callback.answer()

async def handle_sub_add(callback: types.CallbackQuery):
    event_id = callback.data.split(":")[1]
    async with AsyncSessionLocal() as db:
        repo = UserPrefsRepository(db)
        await repo.add_subscription(callback.from_user.id, event_id)
    await callback.answer("\u2705 \u062a\u0645 \u0627\u0644\u0625\u0636\u0627\u0641\u0629 \u0644\u0644\u0641\u0639\u0627\u0644\u064a\u0627\u062a \u0627\u0644\u0645\u062e\u0635\u0635\u0629.")
    await handle_sub_detail(callback)

async def handle_sub_delete(callback: types.CallbackQuery):
    event_id = callback.data.split(":")[1]
    async with AsyncSessionLocal() as db:
        repo = UserPrefsRepository(db)
        await repo.delete_subscription(callback.from_user.id, event_id)
    await callback.answer("\u2705 \u062a\u0645 \u062d\u0630\u0641 \u0627\u0644\u062a\u0646\u0628\u064a\u0647 \u0627\u0644\u0645\u062e\u0635\u0635.")
    await handle_list_custom_events(callback)

async def handle_prompt_event_reminder(callback: types.CallbackQuery, state: FSMContext):
    event_id = callback.data.split(":")[1]
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="\U0001f519 \u0639\u0648\u062f\u0629", callback_data=f"s_det:{event_id}"))
    await safe_send_media(callback, "â° <b>\u0623\u062f\u062e\u0644 \u0648\u0642\u062a \u0627\u0644\u062a\u0630\u0643\u064a\u0631 \u0644\u0647\u0630\u0647 \u0627\u0644\u0641\u0639\u0627\u0644\u064a\u0629 \u0628\u0627\u0644\u0633\u0627\u0639\u0627\u062a:</b>", builder.as_markup())
    await state.update_data(target_event_id=event_id)
    await state.set_state(SniperStates.waiting_for_event_reminder_hours)
    await callback.answer()

async def handle_set_event_reminder(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("\u274c \u064a\u0631\u062c\u0649 \u0625\u062f\u062e\u0627\u0644 \u0631\u0642\u0645 \u0635\u062d\u064a\u062d.")
        return
    
    data = await state.get_data()
    event_id = data.get("target_event_id")
    hours = int(message.text)
    
    async with AsyncSessionLocal() as db:
        repo = UserPrefsRepository(db)
        sub = await repo.get_subscription(message.from_user.id, event_id)
        if sub:
            sub.reminder_time_hours = hours
            await db.commit()
    
    await message.answer(f"\u2705 \u062a\u0645 \u062a\u062d\u062f\u064a\u062b \u0648\u0642\u062a \u0627\u0644\u062a\u0630\u0643\u064a\u0631 \u0644\u0644\u0641\u0639\u0627\u0644\u064a\u0629 \u0625\u0644\u0649 {hours} \u0633\u0627\u0639\u0629.")
    await state.clear()
    await handle_start(message, state)
