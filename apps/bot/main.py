from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis
from core.config.settings import settings
from core.logging.logger import logger
from typing import List
import asyncio
from datetime import datetime, timezone

from apps.bot.handlers import (
    handle_start,
    handle_booking_start,
    handle_browse_org,
    handle_event_detail,
    handle_book_event,
    handle_select_ticket,
    handle_sel_ts,
    handle_sel_team,
    handle_confirm_count,
    handle_execute_booking,
    handle_view_chart,
    handle_speed_book,
    handle_resale_check,
    handle_blacklist_check,
    handle_sub_add_slug,
    handle_event_prefs,
    handle_all_events,
    # Account Management
    list_accounts,
    handle_acc_detail,
    handle_set_role,
    handle_verify_acc,
    handle_verify_all,
    handle_delete_acc,
    handle_link_sniper,
    handle_link_extension,
    # Tasks & Hold
    list_tasks,
    handle_task_detail,
    handle_extend_hold,
    handle_cancel_task,
    handle_payment_link,
    handle_transfer_hold,
    handle_show_hold_token,
    # Settings
    handle_custom_events_menu,
    handle_toggle_global_pref,
    handle_sync_now,
    handle_filter_list,
    handle_toggle_item,
    handle_prompt_reminder,
    handle_set_reminder,
    handle_link_account_prompt,
    handle_token_submission,
    SniperStates
)

from apps.bot.handlers_sub import (
    handle_list_custom_events,
    handle_sub_detail,
    handle_sub_map,
    handle_sub_add,
    handle_sub_delete,
    handle_sub_toggle,
    handle_prompt_event_reminder,
    handle_set_event_reminder
)

# Production Redis Storage with Memory Fallback
try:
    redis_fsm = Redis.from_url(settings.redis_url, decode_responses=True)
    storage = RedisStorage(redis_fsm)
    logger.info("Bot: Initialized REDIS for FSM storage.")
except Exception as e:
    from aiogram.fsm.storage.memory import MemoryStorage
    storage = MemoryStorage()
    logger.warning(f"Bot: Redis unavailable or failed init ({e}). Falling back to MEMORY for FSM storage.")

bot = Bot(token=settings.bot_token)
dp = Dispatcher(storage=storage)

# ── GLOBAL ERROR HANDLER ──
@dp.error()
async def error_handler(event):
    error_text = str(event.exception)
    if "query is too old" in error_text or "query ID is invalid" in error_text:
        logger.warning(f"[CALLBACK_ANSWER_EXPIRED] {event.exception}")
        return True

    logger.critical(f"BOT_FATAL: Unhandled exception in handler: {event.exception}", exc_info=True)
    try:
        if hasattr(event, "update") and event.update.callback_query:
            await event.update.callback_query.answer("⚠️ حدث خطأ فني مفاجئ. تم تسجيل التفاصيل.", show_alert=True)
        elif hasattr(event, "update") and event.update.message:
            await event.update.message.answer("⚠️ حدث خطأ فني مفاجئ. تم تسجيل التفاصيل.")
    except: pass

# ── CORE ──
dp.message.register(handle_start, Command("start"))
dp.callback_query.register(handle_start, F.data == "back_main")

# ── ACCOUNT POOL MANAGEMENT ──
dp.callback_query.register(list_accounts, F.data == "list_accounts")
dp.callback_query.register(handle_acc_detail, F.data.startswith("acc_detail:"))
dp.callback_query.register(handle_set_role, F.data.startswith("set_role:"))
dp.callback_query.register(handle_verify_acc, F.data.startswith("verify_acc:"))
dp.callback_query.register(handle_verify_all, F.data == "verify_all_accounts")
dp.callback_query.register(handle_delete_acc, F.data.startswith("delete_acc:"))
dp.callback_query.register(handle_link_sniper, F.data == "link_sniper")
dp.callback_query.register(handle_link_extension, F.data == "link_extension")
dp.callback_query.register(handle_link_account_prompt, F.data == "link_account_prompt")

# ── TASK MANAGEMENT & HOLD EXTENSION ──
dp.callback_query.register(list_tasks, F.data == "list_tasks")
dp.callback_query.register(handle_task_detail, F.data.startswith("task_detail:"))
dp.callback_query.register(handle_extend_hold, F.data.startswith("extend_hold:"))
dp.callback_query.register(handle_cancel_task, F.data.startswith("cancel_task:"))
dp.callback_query.register(handle_payment_link, F.data.startswith("payment_link:"))
dp.callback_query.register(handle_transfer_hold, F.data.startswith("transfer_hold:"))
dp.callback_query.register(handle_show_hold_token, F.data.startswith("show_hold:"))

# ── BOOKING FLOW ──
dp.callback_query.register(handle_booking_start, F.data == "booking_start")
dp.callback_query.register(handle_browse_org, F.data.startswith("browse_org:"))
dp.callback_query.register(handle_event_detail, F.data.startswith("e_det:"))
dp.callback_query.register(handle_event_detail, F.data.startswith("event_detail:"))
dp.callback_query.register(handle_book_event, F.data.startswith("b_ev:"))
dp.callback_query.register(handle_book_event, F.data.startswith("book_event:"))
dp.callback_query.register(handle_select_ticket, F.data.startswith("sel_t:"))
dp.callback_query.register(handle_confirm_count, F.data.startswith("set_q:"))
dp.callback_query.register(handle_sel_ts, F.data.startswith("sel_ts:"))
dp.callback_query.register(handle_sel_team, F.data.startswith("sel_team:"))
dp.callback_query.register(handle_execute_booking, F.data.startswith("exec_b:"))
dp.callback_query.register(handle_view_chart, F.data.startswith("v_ch:"))
dp.callback_query.register(handle_speed_book, F.data.startswith("s_bk:"))
dp.callback_query.register(handle_resale_check, F.data.startswith("resale_check:"))
dp.callback_query.register(handle_blacklist_check, F.data.startswith("blacklist_check:"))
dp.callback_query.register(handle_sub_add_slug, F.data.startswith("s_ad:"))
dp.callback_query.register(handle_event_prefs, F.data == "event_prefs")
dp.callback_query.register(handle_all_events, F.data == "all_events")

# ── SETTINGS & PREFERENCES ──
dp.callback_query.register(handle_custom_events_menu, F.data == "custom_events_menu")
dp.callback_query.register(handle_toggle_global_pref, F.data.startswith("gpref:"))
dp.callback_query.register(handle_sync_now, F.data == "sync_now")
dp.callback_query.register(handle_filter_list, F.data.startswith("filter_list:"))
dp.callback_query.register(handle_toggle_item, F.data.startswith("toggle_item:"))
dp.callback_query.register(handle_prompt_reminder, F.data == "prompt_reminder")
dp.message.register(handle_set_reminder, SniperStates.waiting_for_reminder_hours)
dp.message.register(handle_token_submission, SniperStates.waiting_for_token)

# ── SUBSCRIBED EVENTS ──
dp.callback_query.register(handle_list_custom_events, F.data == "list_custom_events")
dp.callback_query.register(handle_sub_detail, F.data.startswith("s_det:"))
dp.callback_query.register(handle_sub_map, F.data.startswith("s_map:"))
dp.callback_query.register(handle_sub_add, F.data.startswith("s_add:"))
dp.callback_query.register(handle_sub_delete, F.data.startswith("s_del:"))
dp.callback_query.register(handle_sub_toggle, F.data.startswith("s_tog:"))
dp.callback_query.register(handle_prompt_event_reminder, F.data.startswith("p_rem:"))
dp.message.register(handle_set_event_reminder, SniperStates.waiting_for_event_reminder_hours)

class ServiceManager:
    """
    PHASE 1: Supervised Lifecycle Management.
    Tracks background tasks and prevents orphan processes.
    """
    _tasks: List[asyncio.Task] = []

    @classmethod
    async def start_service(cls, name: str, coro):
        logger.info(f"ServiceManager: Starting {name}...")
        task = asyncio.create_task(coro, name=name)
        cls._tasks.append(task)
        
        def _on_done(t):
            try:
                t.result()
            except asyncio.CancelledError:
                logger.info(f"ServiceManager: {t.get_name()} stopped gracefully.")
            except Exception as e:
                logger.critical(f"ServiceManager: FATAL error in {t.get_name()}: {e}")
        
        task.add_done_callback(_on_done)
        return task

    @classmethod
    async def stop_all(cls):
        logger.info("ServiceManager: Stopping all managed services...")
        for task in cls._tasks:
            if not task.done():
                task.cancel()
        if cls._tasks:
            await asyncio.gather(*cls._tasks, return_exceptions=True)
        cls._tasks.clear()

async def heartbeat_loop():
    """Independent heartbeat for status visibility."""
    from core.database.redis import redis_manager
    while True:
        try:
            await redis_manager.set("system:heartbeat", datetime.now(timezone.utc).isoformat(), ex=600)
        except Exception as e:
            logger.error(f"Heartbeat Error: {e}")
        await asyncio.sleep(30)

async def run_background_services():
    """Autonomous background engine for account health and ghost monitoring."""
    from core.database.postgres import AsyncSessionLocal
    from services.maintenance.health import system_health_monitor
    from services.reservation.reconciler import ReconciliationWorker
    from services.account.manager import AccountManager
    from services.monitor.ghost import GhostMonitor
    from services.reservation.swapper import HoldSwapper
    
    logger.info("🔧 BACKGROUND_SERVICES: Starting autonomous loops...")
    
    # 1. Start Persistent Services
    reconciler = ReconciliationWorker(check_interval=300)
    await ServiceManager.start_service("reconciler", reconciler.run())
    await ServiceManager.start_service("health_monitor", system_health_monitor())
    
    # 2. Start TokenMaster
    swapper = HoldSwapper()
    await ServiceManager.start_service("hold_swapper", swapper.monitor_and_swap())
    
    # 3. Start Ghost Monitor
    ghost = GhostMonitor(None)
    await ServiceManager.start_service("ghost_monitor", ghost.run())

    # 4. Periodic Maintenance Loop
    while True:
        try:
            async with AsyncSessionLocal() as db:
                acc_mgr = AccountManager(db)
                await acc_mgr.verify_all_accounts()
                
                from services.discovery.engine import DiscoveryEngine
                discovery = DiscoveryEngine()
                await discovery.sync_all()

        except Exception as e:
            logger.error(f"Maintenance Loop Error: {e}")
            
        await asyncio.sleep(120)

async def start_bot():
    logger.info("[STARTUP_BEGIN] BOT_START")
    logger.info("ELITE_TERMINAL: Online and Fully Autonomous.")
    
    from services.maintenance.telemetry import telemetry
    
    from core.database.redis import redis_manager
    await redis_manager.set("system:heartbeat", datetime.now(timezone.utc).isoformat(), ex=600)
    await ServiceManager.start_service("heartbeat", heartbeat_loop())
    await ServiceManager.start_service("background_maintenance", run_background_services())
    await ServiceManager.start_service("telemetry", telemetry.run())
    
    # Send today's events notification on startup
    await send_today_events_notification(bot)
    
    try:
        await dp.start_polling(bot)
    finally:
        await ServiceManager.stop_all()
        await bot.session.close()

async def send_today_events_notification(bot: Bot):
    """Send events feed on bot startup - shows upcoming active events."""
    from core.database.postgres import AsyncSessionLocal
    from database.models.discovery import LiveEvent
    from sqlalchemy import select, and_
    from datetime import datetime, timezone, timedelta
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    
    try:
        async with AsyncSessionLocal() as db:
            now = datetime.now(timezone.utc)
            thirty_days = now + timedelta(days=30)
            
            stmt = select(LiveEvent).where(
                and_(
                    LiveEvent.status.in_(["active", "AVAILABLE", "UPCOMING"]),
                    LiveEvent.starts_at >= now,
                    LiveEvent.starts_at <= thirty_days
                )
            ).order_by(LiveEvent.starts_at).limit(20)
            
            result = await db.execute(stmt)
            events = result.scalars().all()
            
            if not events:
                stmt = select(LiveEvent).where(
                    LiveEvent.status.in_(["active", "AVAILABLE", "UPCOMING"])
                ).order_by(LiveEvent.starts_at.desc()).limit(20)
                result = await db.execute(stmt)
                events = result.scalars().all()
            
            if not events:
                return
            
            admin_id = settings.admin_ids[0] if settings.admin_ids else None
            if not admin_id:
                return
            
            summary_text = (
                f"🎯 <b>فعاليات اليوم</b>\n"
                "----------------\n"
            )
            
            builder = InlineKeyboardBuilder()
            for event in events[:50]:
                title = (event.title_ar or event.title_en or event.slug)[:28]
                time_str = event.starts_at.strftime('%H:%M') if event.starts_at else ''
                date_str = event.starts_at.strftime('%m/%d') if event.starts_at else ''
                btn_text = f"{date_str} 📍 {time_str} {title}"
                builder.row(InlineKeyboardButton(text=btn_text, callback_data=f"e_det:{event.slug}"))
            
            await bot.send_message(chat_id=admin_id, text=summary_text, parse_mode="HTML", reply_markup=builder.as_markup())
                
    except Exception as e:
        logger.error(f"[STARTUP_EVENTS_ERROR] {e}")

if __name__ == "__main__":
    try:
        asyncio.run(start_bot())
    except KeyboardInterrupt:
        pass
