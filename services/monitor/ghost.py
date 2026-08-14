import asyncio
import html
import re
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database.models.discovery import LiveEvent, Genre
from modules.webook.client import WebookApiClient
from core.logging.logger import logger


GHOST_SCAN_INTERVAL = 30

from core.utils.encoding import clean_mojibake

def _normalize_telegram_text(text: str) -> str:
    if text is None: return ""
    return clean_mojibake(str(text))

class GhostMonitor:
    """
    THE GHOST MONITOR - Silent Backend Watcher.

    Continuously scans Webook's backend for:
    1. New events that appear before public listing
    2. Ticket availability changes (sold out / available)
    3. Price changes
    4. Date/venue changes

    Generates notification dicts for the Telegram notification engine.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.api = WebookApiClient()
        self._known_slugs = set()
        self._known_prices = {}

    async def initialize(self):
        """Load known state from DB, only loading notified or old historical events."""
        stmt = select(LiveEvent.slug, LiveEvent.min_price, LiveEvent.metadata_json, LiveEvent.synced_at)
        result = await self.db.execute(stmt)
        now_utc = datetime.now(timezone.utc)
        for slug, price, meta_json, synced_at in result:
            meta = meta_json or {}
            is_old = False
            if synced_at:
                if synced_at.tzinfo is None:
                    synced_at = synced_at.replace(tzinfo=timezone.utc)
                if now_utc - synced_at > timedelta(days=1):
                    is_old = True
            
            # If it was already notified, or if it is an old event synced more than 24h ago, count as known
            if meta.get("notified") or is_old:
                self._known_slugs.add(slug)
                self._known_prices[slug] = price

    async def scan_once(self):
        """Execute a single scan iteration. Called externally by ghost_monitor_loop with a fresh session per call."""
        await self.initialize()
        try:
            changes = await self._scan_all_orgs()
            if changes:
                logger.info(f"GhostMonitor: Detected {len(changes)} changes")
                for change in changes:
                    await self._process_change(change)
            self._prune_known_cache()
        except Exception as e:
            logger.error(f"GhostMonitor: Scan failed: {e}")

    async def run(self):
        """Main ghost monitoring loop."""
        from core.database.postgres import AsyncSessionLocal
        logger.info("GhostMonitor: Silent backend watcher STARTED")

        while True:
            try:
                async with AsyncSessionLocal() as db:
                    self.db = db
                    await self.initialize()
                    changes = await self._scan_all_orgs()
                    if changes:
                        logger.info(f"GhostMonitor: Detected {len(changes)} changes")
                        for change in changes:
                            await self._process_change(change)
                    
                    self._prune_known_cache()
                
            except Exception as e:
                logger.error(f"GhostMonitor: Scan failed: {e}")

            await asyncio.sleep(GHOST_SCAN_INTERVAL)

    def _prune_known_cache(self):
        """Prevents memory leak by capping known event tracking."""
        MAX_CACHE = 5000
        if len(self._known_slugs) > MAX_CACHE:
            logger.info(f"GhostMonitor: Pruning cache (Size: {len(self._known_slugs)})")
            self._known_slugs = set(list(self._known_slugs)[-2000:])
            new_prices = {}
            for s in self._known_slugs:
                if s in self._known_prices:
                    new_prices[s] = self._known_prices[s]
            self._known_prices = new_prices

    async def _scan_all_orgs(self) -> list:
        """Scan all organizations for changes."""
        changes = []

        try:
            org_page = 1
            while True:
                org_res = await self.api.get_organizations(page=org_page)
                orgs = org_res.get("data", {}).get("data", [])
                if not orgs: break
                
                for org in orgs:
                    org_slug = org.get("slug")
                    if not org_slug: continue
                    
                    try:
                        result = await self.api.get_events_by_organization(
                            org_slug, lang="ar", per_page=50
                        )
                        events = result.get("events", [])
                        
                        for ev in events:
                            slug = ev.get("slug", "")
                            if not slug: continue
                            
                            if slug not in self._known_slugs:
                                raw_start = ev.get("start_date_time", "")
                                event_start_dt = None
                                formatted_start = "غير محدد"
                                try:
                                    if isinstance(raw_start, (int, float)):
                                        event_start_dt = datetime.fromtimestamp(raw_start, tz=timezone.utc)
                                    elif isinstance(raw_start, str) and raw_start.isdigit():
                                        event_start_dt = datetime.fromtimestamp(int(raw_start), tz=timezone.utc)
                                    elif isinstance(raw_start, str) and raw_start:
                                        clean_ts = raw_start.replace("Z", "+00:00")
                                        event_start_dt = datetime.fromisoformat(clean_ts)
                                    
                                    if event_start_dt:
                                        formatted_start = event_start_dt.strftime("%Y-%m-%d %H:%M")
                                except Exception:
                                    formatted_start = str(raw_start)

                                # Bypass old/historical events starting before yesterday to avoid spamming 2024/2025 alerts
                                now_utc = datetime.now(timezone.utc)
                                if event_start_dt and event_start_dt < now_utc - timedelta(days=1):
                                    logger.info(f"GhostMonitor: Skipping historical event '{ev.get('title')}' starting at {event_start_dt}")
                                    self._known_slugs.add(slug)
                                    continue

                                raw_price = ev.get("min_price")
                                formatted_price = f"{raw_price} SAR" if raw_price else "غير محدد"

                                changes.append({
                                    "type": "NEW_EVENT",
                                    "slug": slug,
                                    "title": ev.get("title", slug),
                                    "org": org_slug,
                                    "venue": ev.get("venue", {}),
                                    "start": formatted_start,
                                    "min_price": formatted_price,
                                    "data": ev,
                                })
                                self._known_slugs.add(slug)

                            if slug in self._known_slugs:
                                stmt = select(LiveEvent).where(LiveEvent.slug == slug)
                                existing = (await self.db.execute(stmt)).scalar_one_or_none()
                                
                                if existing:
                                    new_date = ev.get("start_date_time")
                                    if existing.starts_at and new_date:
                                        dt_new = None
                                        if isinstance(new_date, (int, float)):
                                            dt_new = datetime.fromtimestamp(new_date, tz=timezone.utc)
                                        elif isinstance(new_date, str):
                                            dt_new = datetime.fromisoformat(new_date.replace("Z", "+00:00"))
                                        
                                        if dt_new and existing.starts_at != dt_new:
                                            changes.append({
                                                "type": "DATE_CHANGE",
                                                "slug": slug,
                                                "title": ev.get("title", slug),
                                                "old_val": existing.starts_at.strftime("%Y-%m-%d %H:%M"),
                                                "new_val": dt_new.strftime("%Y-%m-%d %H:%M")
                                            })
                                            existing.starts_at = dt_new

                                    new_venue = ev.get("venue", {}).get("name") if isinstance(ev.get("venue"), dict) else ev.get("venue")
                                    if existing.venue_name and new_venue and existing.venue_name != new_venue:
                                        changes.append({
                                            "type": "LOCATION_CHANGE",
                                            "slug": slug,
                                            "title": ev.get("title", slug),
                                            "old_val": existing.venue_name,
                                            "new_val": new_venue
                                        })
                                        existing.venue_name = new_venue

                                    new_status = ev.get("status", "").upper()
                                    if existing.status and new_status and existing.status != new_status:
                                        if new_status == "AVAILABLE": 
                                            changes.append({
                                                "type": "AVAILABILITY_ALERT",
                                                "slug": slug,
                                                "title": ev.get("title", slug),
                                                "old_val": existing.status,
                                                "new_val": new_status
                                            })
                                        existing.status = new_status
                                    
                                    try:
                                        await self.db.commit()
                                    except Exception as db_err:
                                        await self.db.rollback()
                                        logger.warning(f"Failed to commit updates for slug={slug}: {db_err}")

                            new_price = ev.get("min_price")
                            old_price = self._known_prices.get(slug)
                            if old_price and new_price and old_price != new_price:
                                changes.append({
                                    "type": "PRICE_CHANGE",
                                    "slug": slug,
                                    "title": ev.get("title", slug),
                                    "old_price": old_price,
                                    "new_price": new_price,
                                })
                                if "existing" in locals() and existing:
                                    try:
                                        parsed_new_price = int(float(str(new_price).replace(",", "").strip()))
                                        if existing.min_price != parsed_new_price:
                                            existing.min_price = parsed_new_price
                                            await self.db.commit()
                                    except Exception as db_price_err:
                                        logger.warning(f"Failed to update changed price in DB: {db_price_err}")
                            self._known_prices[slug] = new_price

                    except Exception as e:
                        logger.error(f"GhostMonitor: Sync loop error for {org_slug}: {e}")
                
                if len(orgs) < 100: break
                org_page += 1
                
        except Exception as e:
            logger.error(f"GhostMonitor: Org discovery failed: {e}")

        return changes

    async def _process_change(self, change: dict):
        """Store detected change for notification dispatch."""
        from apps.bot.main import bot
        from core.config.settings import settings
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        from sqlalchemy import select
        from database.models.discovery import LiveEvent
        
        change_type = change["type"]
        slug = change["slug"]

        # Ensure event is persisted first if it is new, to allocate its database ID before constructing buttons
        if change_type == "NEW_EVENT":
            await self._persist_new_event(change)

        # Now fetch the database record to get the auto-incrementing integer ID
        stmt = select(LiveEvent).where(LiveEvent.slug == slug)
        db_event = (await self.db.execute(stmt)).scalar_one_or_none()
        event_ref = str(db_event.id) if db_event else slug

        if change_type == "NEW_EVENT":
            logger.info(f"GhostMonitor: New event '{change['title']}' from {change['org']}")
            
            # Extract poster image
            ev = change.get("data", {})
            img_url = None
            if ev:
                images = ev.get("images", [])
                if isinstance(images, list):
                    # Try to find a mobile_poster or portrait type first
                    for img in images:
                        if isinstance(img, dict):
                            itype = str(img.get("type", "")).lower()
                            if "mobile" in itype or "portrait" in itype or "poster" in itype:
                                img_url = img.get("url")
                                break
                    if not img_url and len(images) > 0:
                        img_url = images[0].get("url")
                if not img_url:
                    img_url = ev.get("mobile_poster") or ev.get("poster") or ev.get("promo_poster")
            
            # Fetch actual event details and tickets dynamically from API to guarantee 1:1 real-time truth!
            tickets = []
            formatted_price = "غير محدد"
            tickets_list = "🎫 لا توجد فئات تذاكر معلنة حالياً\n"
            
            try:
                # Layer 1: Try get_event_tickets endpoint
                tickets_data = await self.api.get_event_tickets(slug)
                if isinstance(tickets_data, dict):
                    tickets = tickets_data.get("event_tickets") or []
                    if not isinstance(tickets, list):
                        tickets = []
                
                # Layer 2: Try get_event_detail page details endpoint
                if not tickets:
                    detail = await self.api.get_event_detail(slug)
                    if isinstance(detail, dict):
                        data_obj = detail.get("data", detail)
                        if isinstance(data_obj, dict):
                            tickets = data_obj.get("event_tickets") or data_obj.get("event_ticket") or data_obj.get("ticket_packages") or data_obj.get("tickets") or []
                            if not isinstance(tickets, list):
                                tickets = []
                
                # Layer 3: Try get_event_availability availability endpoint
                if not tickets:
                    avail_data = await self.api.get_event_availability(slug)
                    if isinstance(avail_data, dict):
                        tickets = avail_data.get("event_tickets") or []
                        if not isinstance(tickets, list):
                            tickets = []
                
                if tickets:
                    min_val = None
                    tickets_list = ""
                    from apps.bot.handlers import ticket_has_available_inventory
                    
                    for t in tickets[:8]:
                        t_name = str(t.get("title") or t.get("name") or "تذكرة").strip()
                        price_val = t.get("price") or t.get("base_price") or 0
                        try:
                            p_val = float(str(price_val).replace(",", "").strip())
                            t_price = f"{p_val * 1.15:,.0f}"
                            if min_val is None or p_val < min_val:
                                min_val = p_val
                        except ValueError:
                            t_price = str(price_val)
                        
                        is_available = ticket_has_available_inventory(t)
                        avail_icon = "🟢" if is_available else "🔴"
                        tickets_list += f"{avail_icon} {t_name} — <b>{t_price} SAR</b>\n"
                    
                    if min_val is not None:
                        formatted_price = f"{min_val * 1.15:,.0f} SAR (شامل الضريبة)"
            except Exception as api_err:
                logger.warning(f"GhostMonitor: Failed to fetch live tickets for {slug}: {api_err}")

            msg = (
                f"🔮 <b>تنبيه: فعالية جديدة!</b>\n"
                f"──────────────────\n"
                f"🎭 <b>{change['title']}</b>\n"
                f"🏢 المنظمة: <code>{change['org']}</code>\n"
                f"💰 السعر الأدنى: <b>{formatted_price}</b>\n"
                f"🕒 البداية: <code>{change['start']}</code>\n\n"
                f"🎫 <b>فئات التذاكر المتاحة:</b>\n"
                f"{tickets_list}"
                f"──────────────────\n"
                f"⚠️ <i>تنبيه! تم اكتشاف هذه الفعالية تلقائياً</i>"
            )
            
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text="🎟 \u0627\u062d\u062c\u0632 \u0627\u0644\u0622\u0646", callback_data=f"b_ev:{event_ref}"),
                        InlineKeyboardButton(text="⚡ \u062d\u062c\u0632 \u0633\u0631\u064a\u0639", callback_data=f"s_bk:{event_ref}")
                    ],
                    [
                        InlineKeyboardButton(text="📡 \u062a\u062a\u0628\u0639 \u0627\u0644\u062a\u0630\u0627\u0643\u0631", callback_data=f"s_ad:{event_ref}"),
                        InlineKeyboardButton(text="🔄 \u062a\u0641\u0627\u0635\u064a\u0644 \u0623\u0643\u062b\u0631", callback_data=f"e_det:{event_ref}")
                    ]
                ]
            )
            await self._broadcast(msg, reply_markup=keyboard, image_url=img_url)

        elif change_type == "PRICE_CHANGE":
            msg = (
                f"\U0001f4b0 <b>\u062a\u0646\u0628\u064a\u0647: \u062a\u063a\u064a\u0631 \u0641\u064a \u0627\u0644\u0623\u0633\u0639\u0627\u0631!</b>\n"
                f"\U0001f3ad {change['title']}\n"
                f"\U0001f4c9 \u0627\u0644\u0633\u0639\u0631 \u0627\u0644\u0642\u062f\u064a\u0645: <code>{change['old_price']} SAR</code>\n"
                f"\U0001f4c8 \u0627\u0644\u0633\u0639\u0631 \u0627\u0644\u062c\u062f\u064a\u062f: <code>{change['new_price']} SAR</code>\n"
                f"\U0001f517 <a href=\"https://webook.com/ar/events/{slug}\">\u0627\u0644\u062a\u0641\u0627\u0635\u064a\u0644</a>"
            )
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text="🔄 \u062a\u0641\u0627\u0635\u064a\u0644 \u0623\u0643\u062b\u0631", callback_data=f"e_det:{event_ref}")
                    ]
                ]
            )
            await self._broadcast(msg, reply_markup=keyboard)

        elif change_type == "DATE_CHANGE":
            msg = (
                f"\U0001f4c5 <b>\u062a\u0646\u0628\u064a\u0647: \u062a\u063a\u064a\u0631 \u0641\u064a \u0627\u0644\u0645\u0648\u0639\u062f!</b>\n"
                f"\U0001f3ad {change['title']}\n"
                f"\u274c \u0627\u0644\u0645\u0648\u0639\u062f \u0627\u0644\u0642\u062f\u064a\u0645: <code>{change['old_val']}</code>\n"
                f"\u2705 \u0627\u0644\u0645\u0648\u0639\u062f \u0627\u0644\u062c\u062f\u064a\u062f: <code>{change['new_val']}</code>\n"
                f"\U0001f517 <a href=\"https://webook.com/ar/events/{slug}\">\u0627\u0644\u062a\u0641\u0627\u0635\u064a\u0644</a>"
            )
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text="🔄 \u062a\u0641\u0627\u0635\u064a\u0644 \u0623\u0643\u062b\u0631", callback_data=f"e_det:{event_ref}")
                    ]
                ]
            )
            await self._broadcast(msg, reply_markup=keyboard)

        elif change_type == "LOCATION_CHANGE":
            msg = (
                f"\U0001f4cd <b>\u062a\u0646\u0628\u064a\u0647: \u062a\u063a\u064a\u0631 \u0641\u064a \u0627\u0644\u0645\u0643\u0627\u0646!</b>\n"
                f"\U0001f3ad {change['title']}\n"
                f"\U0001f3db \u0627\u0644\u0645\u0643\u0627\u0646 \u0627\u0644\u062c\u062f\u064a\u062f: <code>{change['new_val']}</code>\n"
                f"\U0001f517 <a href=\"https://webook.com/ar/events/{slug}\">\u0627\u0644\u062a\u0641\u0627\u0635\u064a\u0644</a>"
            )
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text="🔄 \u062a\u0641\u0627\u0635\u064a\u0644 \u0623\u0643\u062b\u0631", callback_data=f"e_det:{event_ref}")
                    ]
                ]
            )
            await self._broadcast(msg, reply_markup=keyboard)

        elif change_type == "AVAILABILITY_ALERT":
            msg = (
                f"\U0001f7e2 <b>\u062a\u0646\u0628\u064a\u0647: \u062a\u0648\u0641\u0631 \u062a\u0630\u0627\u0643\u0631 \u0641\u062c\u0623\u0629!</b>\n"
                f"\U0001f3ad {change['title']}\n"
                f"\u0627\u0644\u062d\u0627\u0644\u0629: <code>{change['old_val']}</code> \u2794 <b>AVAILABLE</b> \U0001f525\n"
                f"\U0001f517 <a href=\"https://webook.com/ar/events/{slug}\">\u0627\u062d\u062c\u0632 \u0627\u0644\u0622\u0646 \u0645\u062c\u0627\u0646\u0627!</a>"
            )
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text="🎟 \u0627\u062d\u062c\u0632 \u0627\u0644\u0622\u0646", callback_data=f"b_ev:{event_ref}"),
                        InlineKeyboardButton(text="🔄 \u062a\u0641\u0627\u0635\u064a\u0644 \u0623\u0643\u062b\u0631", callback_data=f"e_det:{event_ref}")
                    ]
                ]
            )
            await self._broadcast(msg, reply_markup=keyboard)

    async def _broadcast(self, msg: str, reply_markup=None, image_url: str = None):
        """Send message to all admins and potentially subscribers."""
        from apps.bot.main import bot
        from core.config.settings import settings
        for admin_id in settings.admin_ids:
            try:
                normalized_msg = _normalize_telegram_text(msg)
                if image_url:
                    try:
                        await bot.send_photo(
                            chat_id=admin_id,
                            photo=image_url,
                            caption=normalized_msg,
                            parse_mode="HTML",
                            reply_markup=reply_markup
                        )
                        continue
                    except Exception as photo_err:
                        logger.warning(f"Failed to send photo alert: {photo_err}. Falling back to text.")
                
                await bot.send_message(
                    chat_id=admin_id,
                    text=normalized_msg,
                    parse_mode="HTML",
                    reply_markup=reply_markup
                )
            except Exception as e:
                logger.error(f"Broadcast failed for admin {admin_id}: {e}")

    async def _persist_new_event(self, change: dict):
        """Helper to save new event to DB with secure type safety and flag as notified."""
        ev = change.get("data", {})
        slug = change["slug"]
        stmt = select(LiveEvent).where(LiveEvent.slug == slug)
        existing = (await self.db.execute(stmt)).scalar_one_or_none()
        
        if existing:
            # Event already exists in database (e.g. inserted by sitemap discovery engine first)
            # Update its metadata_json to flag that we have notified the user!
            meta = dict(existing.metadata_json or {})
            meta["notified"] = True
            existing.metadata_json = meta
            try:
                await self.db.commit()
            except Exception as commit_err:
                await self.db.rollback()
                logger.error(f"GhostMonitor: Failed to update notified flag for existing {slug}: {commit_err}")
        else:
            # Create a new event and flag as notified!
            org_slug = change["org"]
            genre_stmt = select(Genre).where(Genre.slug == org_slug)
            genre = (await self.db.execute(genre_stmt)).scalar_one_or_none()
            genre_id = genre.id if genre else None
            
            raw_price = ev.get("min_price")
            parsed_price = None
            if raw_price is not None:
                try:
                    parsed_price = int(float(str(raw_price).replace(",", "").strip()))
                except ValueError:
                    parsed_price = None

            starts_at_val = None
            raw_start = ev.get("start_date_time") or ev.get("startDate")
            if raw_start:
                try:
                    if isinstance(raw_start, (int, float)):
                        starts_at_val = datetime.fromtimestamp(int(raw_start), tz=timezone.utc)
                    elif isinstance(raw_start, str):
                        if raw_start.isdigit():
                            starts_at_val = datetime.fromtimestamp(int(raw_start), tz=timezone.utc)
                        else:
                            starts_at_val = datetime.fromisoformat(raw_start.replace("Z", "+00:00"))
                except Exception:
                    pass

            meta = dict(ev or {})
            meta["notified"] = True

            new_event = LiveEvent(
                webook_id=str(ev.get("_id", "") or f"cf_{slug}"),
                slug=slug,
                title_ar=change["title"],
                title_en=change["title"],
                genre_id=genre_id,
                status="GHOST",
                min_price=parsed_price,
                starts_at=starts_at_val,
                metadata_json=meta,
            )
            self.db.add(new_event)
            try:
                await self.db.commit()
            except Exception as commit_err:
                await self.db.rollback()
                logger.error(f"GhostMonitor: Failed to persist new event {slug}: {commit_err}")

    async def get_pending_notifications(self) -> list:
        """Get ghost-detected events for notification dispatch."""
        stmt = select(LiveEvent).where(LiveEvent.status == "GHOST")
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def check_event_deep(self, slug: str) -> dict:
        """Deep scan a specific event for full availability."""
        detail = await self.api.get_event_detail(slug)
        tickets = await self.api.get_event_tickets(slug)
        resale = await self.api.get_resale_listing(slug)

        return {
            "detail": detail,
            "tickets": tickets,
            "resale": resale,
            "has_chart": bool(detail.get("chart_token") or detail.get("chartToken")),
            "ticket_count": len(tickets.get("data", [])) if isinstance(tickets, dict) else 0,
            "resale_count": len(resale),
        }
