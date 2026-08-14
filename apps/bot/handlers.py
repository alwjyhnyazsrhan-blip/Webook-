from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from core.database.postgres import AsyncSessionLocal
from database.repositories.account import AccountRepository
from database.repositories.reservation import ReservationRepository
from services.discovery.engine import DiscoveryEngine
from services.reservation.orchestrator import ReservationOrchestrator
from database.models.discovery import Genre, LiveEvent, SeatMapCache
from database.models.reservation import TaskStatus
from database.models.account import AuthSession
from database.repositories.user_prefs import UserPrefsRepository
from core.logging.logger import logger
from core.i18n import i18n
from sqlalchemy import select
from datetime import datetime, timezone
import asyncio
import html
import re
import time

def clean_html(text: str) -> str:
    """Safe HTML escaping for Telegram messages."""
    if not text: return ""
    return html.escape(str(text))


_MOJIBAKE_MARKERS = ("Ã", "Â", "â", "ï", "", "Æ", "€")
_MOJIBAKE_REPLACEMENTS = {
    "ÃƒÆ’Ã‚Â¯Ãƒâ€šÃ‚Â¸Ãƒâ€šÃ‚Â": "\ufe0f",
    "ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¯ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¸ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â": "\ufe0f",
    "ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¢Ãƒâ€šÃ‚Â": "•",
    "ÃƒÆ’Ã‚Â¢Ãƒâ€šÃ‚Â Ãƒâ€šÃ‚Â³": "🆕",
    "ÃƒÆ’Ã‚Â¢Ãƒâ€šÃ‚Â Ãƒâ€šÃ‚Â°": "⏳",
    "ÃƒÆ’Ã‚Â¢Ãƒâ€šÃ‚Â Ãƒâ€šÃ‚Â»": "»",
    "ÃƒÆ’Ã‚Â¢Ãƒâ€šÃ‚Â¬Ãƒâ€šÃ‚Â¢": "•",
    "ÃƒÆ’Ã‚Â¯Ãƒâ€šÃ‚Â¿Ãƒâ€šÃ‚Â½": "",
    "Ãƒâ€šÃ‚Â ": " ",
    "Ã‚Â ": " ",
    "Æ’Ã‚Â¢": "",
    "Â¬Ã‚Â¢": "",
    "€šÃ‚Â": "",
    "ÃƒÂ¢Ã¢â‚¬Â Ã¢â€šÂ¬": "─",
    "ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢": "•",
    "ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â": "—",
    "──────────────────": "──────────────────",
}


from core.utils.encoding import clean_mojibake, markdownish_to_html

def normalize_telegram_text(text: str) -> str:
    if text is None: return ""
    text = clean_mojibake(str(text))
    if any(token in text for token in ("**", "`", "_", "](")):
        text = markdownish_to_html(text)
    return text


async def safe_edit_text(message: types.Message, text: str, reply_markup=None, **kwargs):
    text = normalize_telegram_text(text)
    try:
        await message.edit_text(text=text, parse_mode="HTML", reply_markup=reply_markup)
    except Exception as e:
        if "message is not modified" in str(e).lower():
            return
        await message.answer(text, parse_mode="HTML", reply_markup=reply_markup)


async def safe_answer_text(message: types.Message, text: str, reply_markup=None):
    await message.answer(normalize_telegram_text(text), parse_mode="HTML", reply_markup=reply_markup)

async def safe_send_media(callback: types.CallbackQuery, text: str, reply_markup=None, image_url: str = None):
    """
    Harden 1 & 2: Handles photo sending, edit vs send logic, and prevents 'Message Not Modified' crashes.
    """
    text = normalize_telegram_text(text)
    try:
        # If we have an image, we usually want to send a new message and delete the old one
        # to ensure the photo is updated correctly.
        if image_url:
            try:
                logger.info(f"[UX_TRACE] Attempting photo delivery: {image_url[:50]}...")
                await callback.message.answer_photo(
                    photo=image_url,
                    caption=text,
                    parse_mode="HTML",
                    reply_markup=reply_markup
                )
                await callback.message.delete()
                logger.info("[UX_TRACE] Photo delivered, old message deleted.")
                return
            except Exception as e:
                logger.warning(f"[UX_TRACE_FALLBACK] Photo failed ({e}), falling back to text.")
        
        # Fallback to Text Edit
        try:
            await safe_edit_text(callback.message, 
                text=text,
                parse_mode="HTML",
                reply_markup=reply_markup
            )
            logger.info("[UX_TRACE] Message edited successfully.")
        except Exception as e:
            if "message is not modified" in str(e).lower():
                logger.info("[UX_TRACE] Ignored 'Message Not Modified' error.")
            else:
                logger.info("[UX_TRACE_FALLBACK] Edit failed, sending new message.")
                await callback.message.answer(text, parse_mode="HTML", reply_markup=reply_markup)
                
    except Exception as e:
        logger.error(f"[BOT_CRITICAL] safe_send_media totally failed: {e}")

discovery = DiscoveryEngine()

async def resolve_event_slug(value: str) -> str:
    if value and value.isdigit():
        async with AsyncSessionLocal() as db:
            stmt = select(LiveEvent).where(LiveEvent.id == int(value))
            event = (await db.execute(stmt)).scalar_one_or_none()
            return event.slug if event else value
    return value

def elapsed_ms(start: float) -> float:
    return round((time.perf_counter() - start) * 1000, 1)

def extract_ticket_list(tickets_data) -> list:
    if not isinstance(tickets_data, dict):
        return []

    # FIX: Handle both wrapped and unwrapped API responses
    # The API can return: {"event_tickets": [...]} or {"data": {"event_tickets": [...]}} or {"status": "success", "data": {...}}

    # First check for status wrapper
    if tickets_data.get("status") == "success" and tickets_data.get("data"):
        data_obj = tickets_data.get("data", {})
    else:
        data_obj = tickets_data.get("data", tickets_data)

    if isinstance(data_obj, dict):
        # Try multiple keys - the API uses different keys
        tickets = (
            data_obj.get("event_tickets")
            or data_obj.get("event_ticket")
            or data_obj.get("ticket_packages")
            or data_obj.get("tickets")
            or data_obj.get("data", {}).get("event_tickets")
            or []
        )
        if isinstance(tickets, list) and tickets:
            return tickets
        if isinstance(tickets, dict):
            return [tickets]

        # FIX: Also check top-level tickets_data for event_tickets
        top_tickets = (
            tickets_data.get("event_tickets")
            or tickets_data.get("event_ticket")
            or []
        )
        if isinstance(top_tickets, list) and top_tickets:
            return top_tickets

        return []
    if isinstance(data_obj, list):
        return data_obj
    return []

def ticket_has_available_inventory(ticket: dict) -> bool:
    if not isinstance(ticket, dict):
        return False

    def _to_bool(value):
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, str):
            norm = value.strip().lower()
            if norm in ("true", "1", "yes", "y", "on"):
                return True
            if norm in ("false", "0", "no", "n", "off", ""):
                return False
        return None

    def _to_number(value):
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            norm = value.strip().replace(",", "")
            if not norm:
                return None
            try:
                return float(norm)
            except ValueError:
                return None
        return None

    sold_markers = (
        ticket.get("sold_out"),
        ticket.get("is_sold_out"),
        ticket.get("soldOut"),
        ticket.get("isSoldOut"),
    )
    if any(_to_bool(v) is True for v in sold_markers):
        return False

    ticket_status_bool = _to_bool(first_present(ticket.get("ticket_status"), ticket.get("ticketStatus")))
    if ticket_status_bool is False:
        return False

    sale_status = first_present(ticket.get("sale_status"), ticket.get("saleStatus")) or ""
    if isinstance(sale_status, str):
        sale_status_lower = sale_status.lower()
        if any(x in sale_status_lower for x in ("sold", "closed", "ended", "inactive", "paused", "unavailable", "stopped")):
            return False

    status = first_present(ticket.get("status"), ticket.get("sale_status"), ticket.get("saleStatus"))
    if status:
        status_lower = str(status).lower()
        bad_statuses = ("sold", "closed", "ended", "expired", "cancelled", "canceled", "inactive", "paused", "unavailable", "stopped")
        if any(bad in status_lower for bad in bad_statuses):
            return False

    remaining = _to_number(first_present(
        ticket.get("remaining"),
        ticket.get("available"),
        ticket.get("available_quantity"),
        ticket.get("availableQuantity"),
        ticket.get("qty_available"),
    ))
    if remaining is not None:
        return remaining > 0

    capacity = _to_number(first_present(
        ticket.get("capacity"),
        ticket.get("quantity"),
        ticket.get("total_quantity"),
        ticket.get("totalQuantity"),
    ))
    sold = _to_number(first_present(
        ticket.get("sold_quantity"),
        ticket.get("soldQuantity"),
        ticket.get("sold"),
    ))
    if capacity is not None and sold is not None:
        return (capacity - sold) > 0

    availability_hint = _to_bool(first_present(
        ticket.get("is_available"),
        ticket.get("available_for_purchase"),
        ticket.get("can_purchase"),
    ))
    if availability_hint is not None:
        return availability_hint

    # FINAL FALLBACK (Pessimistic)
    # If we have no 'remaining' number, and no explicit 'sold_out' flag,
    # but the status says 'active', we check if it's explicitly bookable.
    is_bookable = _to_bool(first_present(ticket.get("is_bookable"), ticket.get("isBookable")))
    
    has_identity = bool(ticket.get("_id") or ticket.get("id"))
    open_status = (
        (not status or str(status).lower() in ("active", "available", "open", "ongoing", "on_sale", "onsale"))
        and (not sale_status or str(sale_status).lower() in ("active", "available", "open", "ongoing", "on_sale", "onsale"))
        and (ticket_status_bool is not False)
        and (is_bookable is not False)
    )
    
    # If it's a seated event and 'remaining' is None/Missing, we MUST be careful.
    # However, for now we allow it if open_status is True and we have no negative signal.
    if has_identity and open_status:
        # If we reached here, we have no 'remaining' count but status is 'active'
        return True

    return False


def format_price_sar(value, include_tax: bool = True, tax_rate: float = 0.15) -> str:
    try:
        base = float(value)
    except (TypeError, ValueError):
        return str(value) if value is not None else "?"

    total = base * (1.0 + tax_rate) if include_tax else base
    return f"{total:,.2f}"


def build_ticket_snapshot(ticket: dict) -> dict:
    if not isinstance(ticket, dict):
        return {}

    ticket_id = first_present(ticket.get("_id"), ticket.get("id"))
    title = first_present(ticket.get("title"), ticket.get("name"), ticket.get("label"))
    category_key = first_present(
        ticket.get("seats_io_category"),
        ticket.get("seatsIoCategory"),
        ticket.get("category_key"),
        ticket.get("categoryKey"),
    )
    return {
        "ticket_id": str(ticket_id) if ticket_id is not None else None,
        "ticket_title": str(title) if title is not None else None,
        "ticket_slug": str(ticket.get("slug")) if ticket.get("slug") else None,
        "category_key": str(category_key) if category_key is not None else None,
        "category_label": str(title) if title is not None else None,
        "price": first_present(ticket.get("price"), ticket.get("base_price")),
        "remaining": first_present(ticket.get("remaining"), ticket.get("available")),
        "status": first_present(ticket.get("status"), ticket.get("sale_status")),
        "is_available": ticket_has_available_inventory(ticket),
    }


def build_ticket_snapshot_map(tickets: list) -> dict:
    snapshots = {}
    for ticket in tickets:
        snapshot = build_ticket_snapshot(ticket)
        ticket_id = snapshot.get("ticket_id")
        if ticket_id:
            snapshots[str(ticket_id)] = snapshot
    return snapshots

def first_present(*values):
    for value in values:
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        return value
    return None

def nested_value(data, *path):
    current = data
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current

def event_metadata(event: LiveEvent) -> dict:
    meta = event.metadata_json if event and isinstance(event.metadata_json, dict) else {}
    return meta or {}

def event_contentful(event: LiveEvent) -> dict:
    meta = event_metadata(event)
    contentful = meta.get("contentful")
    return contentful if isinstance(contentful, dict) else {}

def image_from_payload(data: dict) -> str:
    if not isinstance(data, dict):
        return None
    images = data.get("images")
    if isinstance(images, list):
        # Try to find a mobile_poster or portrait type first for decent ratio
        for img in images:
            if isinstance(img, dict):
                itype = str(img.get("type", "")).lower()
                if ("mobile" in itype or "portrait" in itype or "poster" in itype) and img.get("url"):
                    return img.get("url")
        # Fallback to any valid image url
        for img in images:
            if isinstance(img, dict) and img.get("url"):
                return img.get("url")
            if isinstance(img, str):
                return img
    return first_present(
        data.get("mobile_poster"),
        data.get("poster"),
        data.get("image_url"),
        data.get("promo_poster"),
        nested_value(data, "image11", "url"),
        nested_value(data, "image31", "url"),
        nested_value(data, "imageBg", "url"),
        nested_value(data, "logo", "url"),
    )

def venue_from_payload(data) -> str:
    if not isinstance(data, dict):
        return data if isinstance(data, str) else None
    venue = data.get("venue")
    if isinstance(venue, dict):
        location = venue.get("location") if isinstance(venue.get("location"), dict) else {}
        return first_present(
            venue.get("name"),
            venue.get("title"),
            venue.get("address"),
            venue.get("description"),
            venue.get("city"),
            location.get("city"),
        )
    if isinstance(venue, str):
        return venue
    zone = data.get("zone")
    if isinstance(zone, dict):
        zone_name = first_present(zone.get("title"), zone.get("name"))
        if zone_name:
            return zone_name
    location = data.get("location")
    if isinstance(location, dict):
        return first_present(location.get("title"), location.get("name"), location.get("city"), location.get("cityCode"))
    return first_present(data.get("venue_name"), data.get("venueName"), data.get("address"), data.get("city"))

def start_from_payload(data):
    if not isinstance(data, dict):
        return None
    schedule = data.get("schedule") if isinstance(data.get("schedule"), dict) else {}
    return first_present(
        data.get("start_date_time"),
        data.get("start_date_time_str"),
        data.get("starts_at"),
        data.get("startDate"),
        data.get("start_date"),
        data.get("booked_from"),
        schedule.get("openDateTime"),
        schedule.get("startDate"),
        schedule.get("start_date_time"),
        data.get("endDate"),
        data.get("end_date_time"),
        schedule.get("closeDateTime"),
    )

def format_event_date(value) -> str:
    if not value:
        return "\u063a\u064a\u0631 \u0645\u062d\u062f\u062f"
    try:
        if isinstance(value, (int, float)):
            value = float(value)
            if value > 10_000_000_000:
                value = value / 1000
            return datetime.fromtimestamp(value, timezone.utc).strftime("%Y-%m-%d %H:%M")
        if isinstance(value, str):
            raw = value.strip()
            if raw.isdigit():
                stamp = int(raw)
                if stamp > 10_000_000_000:
                    stamp = stamp / 1000
                return datetime.fromtimestamp(stamp, timezone.utc).strftime("%Y-%m-%d %H:%M")
            return clean_html(raw[:16].replace("T", " "))
        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return clean_html(str(value))
    return clean_html(str(value))

def extract_detail_fields(detail: dict, event: LiveEvent) -> dict:
    detail = detail if isinstance(detail, dict) else {}
    meta = event_metadata(event)
    contentful = event_contentful(event)
    title = first_present(
        detail.get("title"),
        detail.get("name"),
        meta.get("title"),
        contentful.get("title"),
        event.title_ar if event else None,
    )
    venue = first_present(
        venue_from_payload(detail),
        venue_from_payload(meta),
        venue_from_payload(contentful),
        event.venue_name if event else None,
    )
    start = first_present(
        start_from_payload(detail),
        start_from_payload(meta),
        start_from_payload(contentful),
        event.starts_at if event else None,
    )
    image_url = first_present(
        image_from_payload(detail),
        image_from_payload(meta),
        image_from_payload(contentful),
        event.image_url if event else None,
    )
    return {
        "title": title or (event.slug if event else "event"),
        "venue": venue,
        "date_str": format_event_date(start),
        "image_url": image_url,
        "partial": not bool(venue) or not bool(start),
    }

def normalize_team(raw, fallback_id: str):
    if isinstance(raw, dict):
        name = first_present(raw.get("name"), raw.get("title"), raw.get("label"))
        team_id = first_present(raw.get("_id"), raw.get("id"), raw.get("slug"), fallback_id)
    elif isinstance(raw, str):
        name = raw
        team_id = fallback_id
    else:
        return None
    if not name:
        return None
    safe_id = re.sub(r"[^A-Za-z0-9_-]+", "-", str(team_id or name)).strip("-")[:40] or fallback_id
    return {"id": safe_id, "name": str(name)}

def infer_teams_from_title(title: str) -> list:
    if not title:
        return []
    for separator in [" \u0636\u062f ", " vs ", " VS ", " \u00d7 ", " x "]:
        if separator in title:
            parts = [p.strip(" -\u2013\u2014|") for p in title.split(separator, 1)]
            if len(parts) == 2 and parts[0] and parts[1]:
                left = parts[0].split(" - ")[-1].split(" \u2013 ")[-1].strip()
                right = parts[1].split(" - ")[0].split(" \u2013 ")[0].strip()
                return [normalize_team(left, "home"), normalize_team(right, "away")]
    return []

def extract_team_options(detail: dict, event: LiveEvent = None) -> list:
    detail = detail if isinstance(detail, dict) else {}
    meta = event_metadata(event)
    sources = [detail, meta]
    teams = []
    for source in sources:
        home = normalize_team(source.get("home_team") or source.get("homeTeam"), "home")
        away = normalize_team(source.get("away_team") or source.get("awayTeam"), "away")
        if home and away:
            teams = [home, away]
            break
        for key in ("teams", "competitors"):
            values = source.get(key)
            if isinstance(values, list):
                teams = [team for team in (normalize_team(v, f"team{i}") for i, v in enumerate(values)) if team]
                if len(teams) >= 2:
                    break
        if len(teams) >= 2:
            break
    if len(teams) < 2 and event:
        teams = [team for team in infer_teams_from_title(event.title_ar) if team]
    deduped = []
    seen = set()
    for team in teams:
        if team and team["id"] not in seen:
            deduped.append(team)
            seen.add(team["id"])
    return deduped[:4]

async def get_event_by_slug(slug: str) -> LiveEvent:
    async with AsyncSessionLocal() as db:
        stmt = select(LiveEvent).where(LiveEvent.slug == slug)
        return (await db.execute(stmt)).scalar_one_or_none()

async def hydrate_detail_with_timeout(slug: str, bearer_token: str = None, timeout: int = 15) -> tuple[dict, str]:
    hydration_start = time.perf_counter()
    logger.info(f"[DETAIL_HYDRATION_BEGIN] slug={slug} timeout={timeout}s")
    try:
        detail = await asyncio.wait_for(
            discovery.sync_event_detail(slug, bearer_token=bearer_token),
            timeout=timeout
        )
        logger.info(f"[DETAIL_HYDRATION_SUCCESS] slug={slug} empty={not bool(detail)} took={elapsed_ms(hydration_start)}ms")
        return detail or {}, "success" if detail else "empty"
    except asyncio.TimeoutError:
        logger.error(f"[DETAIL_HYDRATION_TIMEOUT] slug={slug} took={elapsed_ms(hydration_start)}ms")
        return {}, "timeout"
    except Exception as e:
        logger.error(f"[DETAIL_HYDRATION_FAILED] slug={slug} error={e} took={elapsed_ms(hydration_start)}ms", exc_info=True)
        return {}, "failed"

class SniperStates(StatesGroup):
    choosing_event = State()
    choosing_timeslot = State()
    choosing_team = State()
    choosing_category = State()
    choosing_quantity = State()
    waiting_for_token = State()
    waiting_for_reminder_hours = State()
    waiting_for_event_reminder_hours = State()

TASK_STATUS_LABELS = {
    "CREATED": ("🆕", "Initialized", "تم الإنشاء"),
    "AUTH_REQUIRED": ("🔑", "Waiting for session", "في انتظار الجلسة"),
    "QUEUED": ("⏳", "Queued", "في قائمة الانتظار"),
    "PROCESSING": ("⚙️", "Preparing", "جاري التجهيز"),
    "SEARCHING": ("🔍", "Searching seats", "جاري البحث عن مقاعد"),
    "RUNNING": ("⚡", "Sniper Active", "القناص نشط"),
    "HOLDING": ("🔒", "Seats Held", "تم حجز المقاعد مؤقتاً"),
    "RESERVED": ("✅", "Reserved", "تم الحجز بنجاح"),
    "SUCCESS": ("🎉", "Success", "نجاح"),
    "COMPLETED": ("🏁", "Completed", "اكتمل"),
    "FAILED": ("❌", "Failed", "فشل"),
    "RETRYING": ("🔄", "Retrying", "جاري إعادة المحاولة"),
    "EXPIRED": ("💀", "Expired", "انتهت الصلاحية"),
    "CANCELLED": ("🚫", "Cancelled", "تم الإلغاء"),
}

# •••••••••••••••••••••••••••••••••••••••••••
# MAIN DASHBOARD
# •••••••••••••••••••••••••••••••••••••••••••

async def handle_start(message: types.Message):
    async with AsyncSessionLocal() as db:
        repo = UserPrefsRepository(db)
        prefs = await repo.get_global_prefs(message.from_user.id)
        lang = prefs.language or "ar"
        
        acc_repo = AccountRepository(db)
        res_repo = ReservationRepository(db)
        active_accs = len(await acc_repo.get_available_accounts())
        active_tasks = len(await res_repo.get_active_tasks(user_id=message.from_user.id))
    now = datetime.now(timezone.utc)
    visible_events = await discovery.get_all_events(limit=1000)
    
    def is_upcoming(ev):
        if not ev.starts_at: return False
        # Normalize to UTC for comparison
        dt = ev.starts_at
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt >= now

    next_event = next((event for event in visible_events if is_upcoming(event)), None)
    if not next_event and visible_events:
        next_event = visible_events[0]

    builder = InlineKeyboardBuilder()
    if next_event:
        date_str = next_event.starts_at.strftime('%d/%m/%Y') if next_event.starts_at else i18n.t("soon", lang)
        time_str = next_event.starts_at.strftime('%I:%M %p') if next_event.starts_at else '--:--'
        venue_name = next_event.venue_name or '\u2014'
        reminder = (
            f"\U0001f3ad **{next_event.title_ar}**\n"
            f"\U0001f4c5 {i18n.t('date', lang)}: {date_str}\n"
            f"\u23f0 {i18n.t('time', lang)}: {time_str}\n"
            f"\U0001f4cd {i18n.t('venue', lang)}: {venue_name}\n\n"
            f"{i18n.t('book_now', lang)}\n"
        )
        builder.row(
            types.InlineKeyboardButton(text=i18n.t("event_details", lang), callback_data=f"e_det:{next_event.id}"),
            types.InlineKeyboardButton(text=i18n.t("book_now", lang), callback_data=f"b_ev:{next_event.id}")
        )
        builder.row(types.InlineKeyboardButton(text=i18n.t("stop_reminder", lang), callback_data=f"sub_toggle:{next_event.id}:receive_notifications"))
    else:
        reminder = f"\U0001f50e _{i18n.t('no_events_synced', lang)}_\n\n"

    builder.row(types.InlineKeyboardButton(text=i18n.t("start_new_booking", lang), callback_data="booking_start"))
    builder.row(
        types.InlineKeyboardButton(text=i18n.t("all_events", lang), callback_data="all_events"),
        types.InlineKeyboardButton(text=i18n.t("sync", lang), callback_data="sync_now")
    )
    builder.row(
        types.InlineKeyboardButton(text=f"{i18n.t('monitoring', lang)} ({active_tasks})", callback_data="list_tasks"),
        types.InlineKeyboardButton(text=f"{i18n.t('accounts', lang)} ({active_accs})", callback_data="list_accounts")
    )
    builder.row(
        types.InlineKeyboardButton(text=i18n.t("settings", lang), callback_data="custom_events_menu"),
        types.InlineKeyboardButton(text=i18n.t("link_account", lang), callback_data="link_account_prompt")
    )

    from core.database.redis import redis_manager
    dashboard_heartbeat = await redis_manager.get("system:heartbeat")
    is_live = False
    if dashboard_heartbeat:
        try:
            # Force naive comparison for extreme robustness
            hb = datetime.fromisoformat(dashboard_heartbeat).replace(tzinfo=None)
            now_naive = datetime.now(timezone.utc).replace(tzinfo=None)
            if (now_naive - hb).total_seconds() < 600:
                is_live = True
        except Exception as e:
            logger.error(f"Heartbeat Parse Error: {e}")
    
    system_label = i18n.t('system', lang) if lang == 'en' else '\u0627\u0644\u0646\u0638\u0627\u0645'
    status_icon = "🟢" if is_live else "🔴"
    system_status = (i18n.t('system_active', lang) if lang == 'en' else 'نشط') if is_live else (i18n.t('system_standby', lang) if lang == 'en' else 'متوقف')
    system_status = f"{status_icon} {system_status}"
    
    dashboard = (
        f"\U0001f4cc <b>{i18n.t('upcoming_event_reminder', lang)}</b>\n{reminder}"
        f"\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n"
        f"<code>{system_label}  :</code> {system_status}\n"
        f"<code>{i18n.t('sessions', lang)}:</code> {active_accs} {i18n.t('verified', lang)}\n"
        f"<code>{i18n.t('missions', lang)}:</code> {active_tasks} {i18n.t('running', lang)}\n"
    )
    target = message.answer if isinstance(message, types.Message) else None
    logger.info(f"[UX_TRACE] Sending Main Menu to user_id={message.from_user.id}")
    
    if target:
        await target(dashboard, parse_mode="HTML", reply_markup=builder.as_markup())
    else:
        await safe_send_media(message, dashboard, builder.as_markup())

# •••••••••••••••••••••••••••••••••••••••••••
# BOOKING FLOW: Dynamic, zero hardcoding
# Step 1: Choose Organization/Category (LIVE from DB)
# Step 2: Choose Event (LIVE from DB)
# Step 3: View Event Detail (LIVE from API)
# Step 4: View Tickets (LIVE from API)
# •••••••••••••••••••••••••••••••••••••••••••

async def handle_booking_start(callback: types.CallbackQuery, state: FSMContext):
    logger.info(f"[CALLBACK_RECEIVED] booking_start | user_id={callback.from_user.id}")
    await state.clear()
    try:
        from services.discovery.navigation import get_nav_categories
        categories = await get_nav_categories()
        
        builder = InlineKeyboardBuilder()
        if not categories:
            await safe_edit_text(callback.message, "⚠️ لا توجد فعاليات متاحة حالياً.\nاضغط تحديث لمزامنة البيانات.", reply_markup=InlineKeyboardBuilder().row(
                types.InlineKeyboardButton(text="🔄 تحديث", callback_data="sync_now"),
                types.InlineKeyboardButton(text="🔙 عودة", callback_data="back_main")
            ).as_markup())
            await callback.answer()
            return
        
        for cat in categories:
            label = f"{cat.icon} {cat.label_ar} ({cat.event_count})"
            builder.row(types.InlineKeyboardButton(
                text=label,
                callback_data=f"browse_org:{cat.key}"
            ))
        
        builder.row(types.InlineKeyboardButton(text="🔙 عودة", callback_data="back_main"))
        await safe_send_media(
            callback,
            "🎯 <b>اختر التصنيف:</b>\n<i>جميع البيانات مزامنة من webook.com</i>",
            builder.as_markup(),
        )
        await callback.answer()
        logger.info(f"[HANDLER_SUCCESS] handle_booking_start | categories={len(categories)}")
    except Exception as e:
        logger.error(f"[HANDLER_EXCEPTION] handle_booking_start: {e}", exc_info=True)
        await callback.answer("❌ حدث خطأ داخلي")

async def handle_browse_org(callback: types.CallbackQuery, state: FSMContext):
    logger.info(f"[CALLBACK_RECEIVED] {callback.data} | user_id={callback.from_user.id}")
    try:
        nav_key = callback.data.split(":")[1]
        logger.info(f"[ROUTER_MATCHED] browse_org | nav_key={nav_key}")
        
        # Football has sub-navigation (clubs)
        if nav_key == "football":
            from services.discovery.navigation import get_football_subcategories
            subs = await get_football_subcategories()
            builder = InlineKeyboardBuilder()
            if not subs:
                builder.row(types.InlineKeyboardButton(text="🔙 عودة", callback_data="booking_start"))
                await safe_send_media(callback, "⚠️ لا توجد مباريات كرة قدم متاحة حالياً.", builder.as_markup())
                await callback.answer()
                return
            for sub in subs:
                builder.row(types.InlineKeyboardButton(
                    text=f"{sub.icon} {sub.label_ar} ({sub.event_count})",
                    callback_data=f"browse_org:{sub.key}"
                ))
            builder.row(types.InlineKeyboardButton(text="🔙 عودة", callback_data="booking_start"))
            await safe_send_media(callback, "⚽ <b>كرة القدم</b>\n<i>اختر الفريق أو عرض جميع المباريات:</i>", builder.as_markup())
            await callback.answer()
            return
        
        # Club-level view (e.g. al-hilal, al-nassr)
        from services.discovery.navigation import get_events_for_club, get_events_for_nav_category, CLUB_ICONS
        
        if nav_key == "all_football":
            events = await get_events_for_nav_category("football")
            section_title = "⚽ جميع مباريات كرة القدم"
        elif nav_key in CLUB_ICONS:
            events = await get_events_for_club(nav_key)
            section_title = f"{CLUB_ICONS.get(nav_key, '⚽')} مباريات {nav_key}"
        else:
            events = await get_events_for_nav_category(nav_key)
            from services.discovery.navigation import CATEGORY_ICONS
            icon = CATEGORY_ICONS.get(nav_key, "📌")
            section_title = f"{icon} {nav_key}"
        
        builder = InlineKeyboardBuilder()
        if not events:
            builder.row(types.InlineKeyboardButton(text="🔙 عودة", callback_data="booking_start"))
            await safe_send_media(callback, f"⚠️ لا توجد فعاليات متاحة في هذا التصنيف حالياً.", builder.as_markup())
            await callback.answer()
            return
            
        for ev in events[:25]:
            date_label = ev.starts_at.strftime('%m/%d') if ev.starts_at else ''
            status_icon = "🟢" if ev.status in ("AVAILABLE", "UPCOMING", "UNKNOWN", None) else "🔴"
            title = (ev.title_ar or ev.title_en or ev.slug)[:45]
            price_label = f" | {format_price_sar(ev.min_price)}" if ev.min_price else ""
            builder.row(types.InlineKeyboardButton(
                text=f"{status_icon} {title} {date_label}{price_label}",
                callback_data=f"e_det:{ev.id}"
            ))
        
        # Smart back button: clubs go back to football, categories go to main
        if nav_key in CLUB_ICONS or nav_key == "all_football":
            builder.row(types.InlineKeyboardButton(text="🔙 عودة", callback_data="browse_org:football"))
        else:
            builder.row(types.InlineKeyboardButton(text="🔙 عودة", callback_data="booking_start"))
        
        await safe_send_media(callback, f"📡 <b>{clean_html(section_title)}</b>\n<i>اختر الفعالية للتفاصيل</i>", builder.as_markup())
        await callback.answer()
        logger.info(f"[HANDLER_SUCCESS] handle_browse_org | nav_key={nav_key} events={len(events)}")
    except Exception as e:
        logger.error(f"[HANDLER_EXCEPTION] handle_browse_org: {e}", exc_info=True)
        await callback.answer("❌ حدث خطأ داخلي")

async def handle_sel_ts(callback: types.CallbackQuery, state: FSMContext):
    ts_id = callback.data.split(":")[1]
    await state.update_data(timeslot_id=ts_id)
    data = await state.get_data()
    detail = await discovery.sync_event_detail(data["slug"])
    await proceed_to_teams(callback, state, detail)

async def handle_sel_team(callback: types.CallbackQuery, state: FSMContext):
    team_id = callback.data.split(":")[1]
    await state.update_data(team_id=team_id)
    data = await state.get_data()
    await proceed_to_categories(callback, state, data["slug"])

async def handle_select_ticket(callback: types.CallbackQuery, state: FSMContext):
    """Step 4: Quantity selection."""
    ticket_id = callback.data.split(":")[1]
    data = await state.get_data()
    slug = data.get("slug")
    ticket_snapshots = data.get("ticket_snapshots") if isinstance(data.get("ticket_snapshots"), dict) else {}
    ticket_snapshot = ticket_snapshots.get(str(ticket_id)) or {"ticket_id": str(ticket_id), "ticket_title": str(ticket_id)}
    await state.update_data(ticket_id=ticket_id, ticket_snapshot=ticket_snapshot)
    await state.set_state(SniperStates.choosing_quantity)
    
    builder = InlineKeyboardBuilder()
    for i in range(1, 6):
        builder.button(text=str(i), callback_data=f"set_q:{i}")
    builder.adjust(3)
    builder.row(types.InlineKeyboardButton(text="\U0001f519 \u0639\u0648\u062f\u0629", callback_data=f"b_ev:{slug}"))
    await safe_send_media(callback, "\U0001f522 <b>\u0643\u0645 \u0639\u062f\u062f \u0627\u0644\u062a\u0630\u0627\u0643\u0631 \u0627\u0644\u0645\u0637\u0644\u0648\u0628 \u062d\u062c\u0632\u0647\u0627\u061f</b>", builder.as_markup())
    await callback.answer()

async def handle_confirm_count(callback: types.CallbackQuery, state: FSMContext):
    """Step 5: Mission Summary."""
    raw_count = callback.data.split(":")[1]
    try:
        count_int = max(1, min(5, int(raw_count)))
    except Exception:
        count_int = 1
    count = str(count_int)
    await state.update_data(count=count)
    data = await state.get_data()
    slug = data.get("slug")
    ticket_id = data.get("ticket_id")
    ticket_snapshot = data.get("ticket_snapshot") or {}
    
    # Recovery: If ticket_id is missing from state, try to get it from snapshot
    if not ticket_id and ticket_snapshot.get("ticket_id"):
        ticket_id = ticket_snapshot["ticket_id"]
        await state.update_data(ticket_id=ticket_id)

    if not ticket_id:
        logger.error(f"[BOT_QTY_FAIL] ticket_id missing from state for slug={slug}")
        await callback.answer("⚠️ حدث خطأ في استعادة بيانات التذكرة. يرجى المحاولة مرة أخرى.", show_alert=True)
        return

    ticket_label = clean_html(
        ticket_snapshot.get("ticket_title") 
        or ticket_snapshot.get("category_label") 
        or str(ticket_id) 
        or "-"
    )

    timeslot_label = data.get('timeslot_id', '\u0627\u0644\u0627\u0641\u062a\u0631\u0627\u0636\u064a')
    team_label = data.get('team_id', '\u0623\u064a \u0645\u0643\u0627\u0646')
    
    text = (
        f"\U0001f680 <b>\u062a\u0623\u0643\u064a\u062f \u0645\u0647\u0645\u0629 \u0627\u0644\u0642\u0646\u0635</b>\n"
        f"\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n"
        f"\U0001f3ad \u0627\u0644\u0641\u0639\u0627\u0644\u064a\u0629: <code>{clean_html(slug)}</code>\n"
        f"\U0001f4c5 \u0627\u0644\u0645\u0648\u0639\u062f: <code>{clean_html(timeslot_label)}</code>\n"
        f"\u26bd \u0627\u0644\u0641\u0631\u064a\u0642: <code>{clean_html(team_label)}</code>\n"
        f"\U0001f3ab \u0627\u0644\u0641\u0626\u0629: {ticket_label}\n"
        f"\U0001f522 \u0627\u0644\u0639\u062f\u062f: <code>{count}</code>\n"
        f"⚠️ <b>بمجرد البدء، سيقوم البوت بمراقبة السيرفر مباشرة وتجاوز الطوابير لاقتناص هذه المواصفات بدقة.</b>"
    )

    # Create the task in CREATED state to preserve parameters (bypasses 64-byte Telegram limit)
    async with AsyncSessionLocal() as db:
        from database.models.reservation import ReservationTask, TaskStatus
        selection_context = {
            "ticket_id": str(ticket_id) if ticket_id is not None else None,
            "ticket_title": ticket_snapshot.get("ticket_title") or ticket_snapshot.get("category_label"),
            "ticket_slug": ticket_snapshot.get("ticket_slug"),
            "category_key": ticket_snapshot.get("category_key"),
            "category_label": ticket_snapshot.get("category_label") or ticket_snapshot.get("ticket_title"),
            "timeslot_id": data.get("timeslot_id"),
            "team_id": data.get("team_id"),
        }
        import uuid
        operation_uuid = str(uuid.uuid4())
        task = ReservationTask(
            operation_uuid=operation_uuid,
            fencing_token=1, # Initial lease version

            user_id=callback.from_user.id,
            event_slug=slug,
            category=selection_context.get("category_label") or selection_context.get("ticket_title") or str(ticket_id),
            seat_count=int(count),
            timeslot_id=data.get("timeslot_id"),
            team_id=data.get("team_id"),
            status=TaskStatus.CREATED.value,
            execution_logs=[{
                "ts": datetime.now(timezone.utc).isoformat(),
                "msg": "SELECTION_CONTEXT",
                "selection_context": selection_context,
            }],
        )
        db.add(task)
        await db.commit()
        task_id = task.id

    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="\u26a1 \u0627\u0628\u062f\u0623 \u0627\u0644\u0642\u0646\u0635 \u0627\u0644\u0622\u0646!", callback_data=f"exec_b:{task_id}"))
    builder.row(types.InlineKeyboardButton(text="\u274c \u0627\u0644\u063a\u0627\u0621 \u0648\u0627\u0644\u0639\u0648\u062f\u0629", callback_data=f"sel_t:{ticket_id}"))
    await safe_send_media(callback, text, builder.as_markup())
    await callback.answer()

async def handle_execute_booking(callback: types.CallbackQuery, state: FSMContext):
    """Step 7: Execute the reservation via orchestrator."""
    # Recover Task ID from callback
    parts = callback.data.split(":")
    task_id = int(parts[1]) if len(parts) > 1 else None

    if not task_id:
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="\U0001f519 \u0639\u0648\u062f\u0629", callback_data="back_main"))
        logger.error(f"[RESERVE_CALLBACK] task_id=None user_id={callback.from_user.id} error=MISSING_TASK_ID")
        await safe_send_media(callback, "\u274c \u062e\u0637\u0623 \u0641\u064a \u0627\u0644\u0646\u0638\u0627\u0645: \u0644\u0645 \u064a\u062a\u0645 \u0627\u0644\u0639\u062b\u0648\u0631 \u0639\u0644\u0649 \u0627\u0644\u0645\u0647\u0645\u0629.", builder.as_markup())
        return

    logger.info(f"[RESERVE_CALLBACK] user_id={callback.from_user.id} task_id={task_id}")
    # REAL validation: check accounts before executing
    async with AsyncSessionLocal() as db:
        acc_repo = AccountRepository(db)
        account = await acc_repo.get_sniper_account()
        logger.info(
            f"[RESERVE_ACCOUNT_CHECK] task_id={task_id} ok={bool(account)} "
            f"account_id={account.id if account else None} health={account.health if account else None} "
            f"is_active={account.is_active if account else None}"
        )
        if not account:
            # Update task status to AUTH_REQUIRED to signal desync
            from database.models.reservation import TaskStatus
            task = await db.get(ReservationTask, task_id)
            if task:
                task.status = TaskStatus.AUTH_REQUIRED.value
                task.execution_logs.append({
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "msg": "EXECUTION_HALTED: No active session found. Redirecting to auth."
                })
                await db.commit()

            builder = InlineKeyboardBuilder()
            builder.row(types.InlineKeyboardButton(text="🔑 ربط حساب Webook", callback_data="link_account_prompt"))
            builder.row(types.InlineKeyboardButton(text="🔙 عودة", callback_data="back_main"))
            logger.error(f"[RESERVE_NO_ACCOUNT] task_id={task_id} user_id={callback.from_user.id}")
            await safe_send_media(
                callback,
                "❌ <b>لا يمكن تنفيذ الحجز</b>\n"
                "تم تعليق المهمة مؤقتاً لأنك لا تملك حساباً نشطاً.\n"
                "يرجى ربط حسابك بالـ <code>Bearer Token</code> للمتابعة.",
                builder.as_markup()
            )
            return

        try:
            builder_load = InlineKeyboardBuilder()
            builder_load.row(types.InlineKeyboardButton(text="\U0001f519 \u0625\u0644\u063a\u0627\u0621", callback_data="back_main"))
            await safe_send_media(callback, "\U0001f504 <b>\u062c\u0627\u0631\u064a \u0625\u0637\u0644\u0627\u0642 \u0645\u0647\u0645\u0629 \u0627\u0644\u062d\u062c\u0632...</b>\n\u064a\u0631\u062c\u0649 \u0627\u0644\u0627\u0646\u062a\u0638\u0627\u0631...", builder_load.as_markup())
            
            orch = ReservationOrchestrator(db)
            logger.info(f"[RESERVE_ORCHESTRATOR_CALL] task_id={task_id} user_id={callback.from_user.id}")
            task = await orch.start_reservation(
                user_id=callback.from_user.id,
                task_id=task_id
            )
            logger.info(f"[RESERVE_ORCHESTRATOR_OK] task_id={task_id} status={task.status} account_id={task.account_id}")
            builder = InlineKeyboardBuilder()
            builder.row(types.InlineKeyboardButton(text="\U0001f4ca \u0627\u0644\u0645\u0631\u0627\u0642\u0628\u0629", callback_data="list_tasks"))
            builder.row(types.InlineKeyboardButton(text="\U0001f519 \u0627\u0644\u0642\u0627\u0626\u0645\u0629 \u0627\u0644\u0631\u0626\u064a\u0633\u064a\u0629", callback_data="back_main"))
            await safe_send_media(
                callback,
                f"\u2705 <b>\u062a\u0645 \u0625\u0637\u0644\u0627\u0642 \u0645\u0647\u0645\u0629 \u0627\u0644\u062d\u062c\u0632</b>\n"
                f"ID: #{task.id}\n"
                f"\u0627\u0644\u062d\u0627\u0644\u0629: {task.status} \U0001f7e2\n"
                f"\u0627\u0644\u0628\u0648\u062a \u064a\u0631\u0627\u0642\u0628 \u0627\u0644\u0633\u064a\u0631\u0641\u0631 \u0627\u0644\u0622\u0646...",
                builder.as_markup()
            )
        except Exception as e:
            builder = InlineKeyboardBuilder()
            builder.row(types.InlineKeyboardButton(text="\U0001f519 \u0639\u0648\u062f\u0629", callback_data="back_main"))
            logger.exception(f"[RESERVE_ORCHESTRATOR_EXCEPTION] task_id={task_id} class={e.__class__.__name__} error={e}")
            await safe_send_media(callback, f"\u274c \u0641\u0634\u0644 \u062a\u0646\u0641\u064a\u0630 \u0627\u0644\u062d\u062c\u0632: {clean_html(str(e))}", builder.as_markup())
    await state.clear()
    await callback.answer()

# •••••••••••••••••••••••••••••••••••••••••••
# ACCOUNTS PANEL (Full Pool Management)
# •••••••••••••••••••••••••••••••••••••••••••

async def list_accounts(callback: types.CallbackQuery):
    """Full account pool dashboard with roles, holds, and actions."""
    from services.account.manager import AccountManager
    from database.models.account import AccountRole
    async with AsyncSessionLocal() as db:
        mgr = AccountManager(db)
        pool = await mgr.get_pool_summary()

    total = pool["total"]
    sniper = pool["sniper"]
    extension = pool["extension"]
    monitor_count = pool["monitor"]
    holding = pool["holding"]

    text = (
        f"\U0001f464 **\u0645\u062f\u064a\u0631 \u0627\u0644\u062d\u0633\u0627\u0628\u0627\u062a**\n"
        f"••••••••••••••••••\n"
        f"\U0001f4ca \u0627\u0644\u0627\u062c\u0645\u0627\u0644\u064a: {total}\n"
        f"\U0001f3af \u062d\u0633\u0627\u0628\u0627\u062a \u0627\u0644\u0642\u0646\u0635: {sniper}\n"
        f"\U0001f504 \u062d\u0633\u0627\u0628\u0627\u062a \u0627\u0644\u062a\u0645\u062f\u064a\u062f: {extension}\n"
        f"\U0001f47b \u062d\u0633\u0627\u0628\u0627\u062a \u0627\u0644\u0645\u0631\u0627\u0642\u0628\u0629: {monitor_count}\n"
        f"\U0001f512 \u064a\u062d\u062a\u062c\u0632 \u062a\u0630\u0627\u0643\u0631: {holding}\n"
        f"••••••••••••••••••\n"
    )

    builder = InlineKeyboardBuilder()

    # List each account with quick actions
    for acc in pool["accounts"][:15]:
        role_icon = {"SNIPER": "\U0001f3af", "EXTENSION": "\U0001f504", "MONITOR": "\U0001f47b"}.get(acc.role, "\U0001f464")
        hold_icon = "\U0001f512" if acc.current_hold_event else ""
        builder.row(types.InlineKeyboardButton(
            text=f"{role_icon} {acc.email} {hold_icon}",
            callback_data=f"acc_detail:{acc.id}"
        ))

    builder.row(
        types.InlineKeyboardButton(text="\U0001f517 \u0631\u0628\u0637 \u062d\u0633\u0627\u0628 \u0642\u0646\u0635", callback_data="link_sniper"),
        types.InlineKeyboardButton(text="\U0001f517 \u0631\u0628\u0637 \u062d\u0633\u0627\u0628 \u062a\u0645\u062f\u064a\u062f", callback_data="link_extension")
    )
    builder.row(types.InlineKeyboardButton(text="\u2705 \u062a\u062d\u0642\u0642 \u0645\u0646 \u062c\u0645\u064a\u0639 \u0627\u0644\u062d\u0633\u0627\u0628\u0627\u062a", callback_data="verify_all_accounts"))
    builder.row(types.InlineKeyboardButton(text="\U0001f519 \u0639\u0648\u062f\u0629", callback_data="back_main"))
    await safe_edit_text(callback.message, text, builder.as_markup())
    await callback.answer()

async def handle_acc_detail(callback: types.CallbackQuery):
    """Individual account detail with management options."""
    acc_id = int(callback.data.split(":")[1])
    async with AsyncSessionLocal() as db:
        acc = await db.get(AuthSession, acc_id)
        if not acc:
            await callback.answer("\u0627\u0644\u062d\u0633\u0627\u0628 \u063a\u064a\u0631 \u0645\u0648\u062c\u0648\u062f")
            return

    role_name = {"SNIPER": "\u0642\u0646\u0635", "EXTENSION": "\u062a\u0645\u062f\u064a\u062f", "MONITOR": "\u0645\u0631\u0627\u0642\u0628\u0629"}.get(acc.role, acc.role)
    hold_info = f"\n\U0001f512 \u064a\u062d\u062a\u062c\u0632: {acc.current_hold_event}" if acc.current_hold_event else ""
    expires = f"\nÃƒÆ’Ã‚Â¢Ãƒâ€šÃ‚ÂÃƒâ€šÃ‚Â° \u064a\u0646\u062a\u0647\u064a: {acc.hold_expires_at.strftime('%H:%M:%S')}" if acc.hold_expires_at else ""

    text = (
        f"\U0001f464 **\u062a\u0641\u0627\u0635\u064a\u0644 \u0627\u0644\u062d\u0633\u0627\u0628**\n"
        f"••••••••••••••••••\n"
        f"\U0001f4e7 {acc.email}\n"
        f"\U0001f4f1 {acc.phone or '--'}\n"
        f"\U0001f464 {acc.first_name or ''} {acc.last_name or ''}\n"
        f"\U0001f3f7 \u0627\u0644\u062f\u0648\u0631: {role_name}\n"
        f"\U0001f49a \u0627\u0644\u062d\u0627\u0644\u0629: {acc.health}\n"
        f"\U0001f4ca \u0627\u062c\u0645\u0627\u0644\u064a \u0627\u0644\u062d\u062c\u0648\u0632\u0627\u062a: {acc.total_bookings}\n"
        f"{hold_info}{expires}\n"
    )

    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="\u2705 \u062a\u062d\u0642\u0642 \u0645\u0646 \u0627\u0644\u062a\u0648\u0643\u0646", callback_data=f"verify_acc:{acc_id}"))
    builder.row(
        types.InlineKeyboardButton(text="\U0001f3af \u062c\u0639\u0644\u0647 \u0642\u0646\u0635", callback_data=f"set_role:{acc_id}:SNIPER"),
        types.InlineKeyboardButton(text="\U0001f504 \u062c\u0639\u0644\u0647 \u062a\u0645\u062f\u064a\u062f", callback_data=f"set_role:{acc_id}:EXTENSION"),
        types.InlineKeyboardButton(text="\U0001f47b \u062c\u0639\u0644\u0647 \u0645\u0631\u0627\u0642\u0628", callback_data=f"set_role:{acc_id}:MONITOR"),
    )
    if acc.current_hold_event:
        builder.row(types.InlineKeyboardButton(text="ÃƒÆ’Ã‚Â¢Ãƒâ€šÃ‚ÂÃƒâ€šÃ‚Â° \u062a\u0645\u062f\u064a\u062f \u0627\u0644\u062d\u062c\u0632", callback_data=f"extend_hold_acc:{acc_id}"))
    builder.row(types.InlineKeyboardButton(text="\u274c \u062d\u0630\u0641 \u0627\u0644\u062d\u0633\u0627\u0628", callback_data=f"delete_acc:{acc_id}"))
    builder.row(types.InlineKeyboardButton(text="\U0001f519 \u0639\u0648\u062f\u0629", callback_data="list_accounts"))
    await safe_edit_text(callback.message, text, builder.as_markup())
    await callback.answer()

async def handle_set_role(callback: types.CallbackQuery):
    parts = callback.data.split(":")
    acc_id, role = int(parts[1]), parts[2]
    async with AsyncSessionLocal() as db:
        repo = AccountRepository(db)
        await repo.set_role(acc_id, role)
    role_ar = {"SNIPER": "\u0642\u0646\u0635", "EXTENSION": "\u062a\u0645\u062f\u064a\u062f", "MONITOR": "\u0645\u0631\u0627\u0642\u0628\u0629"}.get(role, role)
    await callback.answer(f"\u2705 \u062a\u0645 \u062a\u063a\u064a\u064a\u0631 \u0627\u0644\u062f\u0648\u0631 \u0627\u0644\u0649 {role_ar}")
    # Refresh the detail page
    callback.data = f"acc_detail:{acc_id}"
    await handle_acc_detail(callback)

async def handle_verify_acc(callback: types.CallbackQuery):
    acc_id = int(callback.data.split(":")[1])
    from services.account.manager import AccountManager
    async with AsyncSessionLocal() as db:
        mgr = AccountManager(db)
        ok = await mgr.verify_account(acc_id)
    await callback.answer("\u2705 \u0627\u0644\u062a\u0648\u0643\u0646 \u0635\u0627\u0644\u062d!" if ok else "\u274c \u0627\u0644\u062a\u0648\u0643\u0646 \u0645\u0646\u062a\u0647\u064a")
    callback.data = f"acc_detail:{acc_id}"
    await handle_acc_detail(callback)

async def handle_verify_all(callback: types.CallbackQuery):
    from services.account.manager import AccountManager
    builder_load = InlineKeyboardBuilder()
    builder_load.row(types.InlineKeyboardButton(text="\U0001f519 \u0625\u0644\u063a\u0627\u0621", callback_data="list_accounts"))
    await safe_edit_text(
        callback.message,
        "\U0001f504 **\u062c\u0627\u0631\u064a \u0627\u0644\u062a\u062d\u0642\u0642 \u0645\u0646 \u062c\u0645\u064a\u0639 \u0627\u0644\u062d\u0633\u0627\u0628\u0627\u062a...**",
        builder_load.as_markup(),
    )
    async with AsyncSessionLocal() as db:
        mgr = AccountManager(db)
        results = await mgr.verify_all_accounts()
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="\U0001f519 \u0639\u0648\u062f\u0629", callback_data="list_accounts"))
    await safe_edit_text(
        callback.message,
        f"\u2705 **\u0646\u062a\u0627\u0626\u062c \u0627\u0644\u062a\u062d\u0642\u0642:**\n"
        f"\u0646\u0634\u0637: {results['active']}\n"
        f"\u0645\u0646\u062a\u0647\u064a: {results['expired']}\n"
        f"\u0627\u0644\u0627\u062c\u0645\u0627\u0644\u064a: {results['total']}",
        builder.as_markup(),
    )
    await callback.answer()

async def handle_delete_acc(callback: types.CallbackQuery):
    acc_id = int(callback.data.split(":")[1])
    async with AsyncSessionLocal() as db:
        acc = await db.get(AuthSession, acc_id)
        if acc:
            await db.delete(acc)
            await db.commit()
    await callback.answer("\u2705 \u062a\u0645 \u062d\u0630\u0641 \u0627\u0644\u062d\u0633\u0627\u0628")
    await list_accounts(callback)

async def handle_link_sniper(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(link_role="SNIPER")
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="\U0001f519 \u0639\u0648\u062f\u0629", callback_data="list_accounts"))
    await safe_edit_text(
        callback.message,
        "\U0001f3af **\u0631\u0628\u0637 \u062d\u0633\u0627\u0628 \u0642\u0646\u0635:**\n\u0627\u0631\u0633\u0644 \u0627\u0644\u0640 `Bearer Token` \u0627\u0644\u062e\u0627\u0635 \u0628\u0627\u0644\u062d\u0633\u0627\u0628.",
        builder.as_markup(),
    )
    await state.set_state(SniperStates.waiting_for_token)
    await callback.answer()

async def handle_link_extension(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(link_role="EXTENSION")
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="\U0001f519 \u0639\u0648\u062f\u0629", callback_data="list_accounts"))
    await safe_edit_text(
        callback.message,
        "\U0001f504 **\u0631\u0628\u0637 \u062d\u0633\u0627\u0628 \u062a\u0645\u062f\u064a\u062f:**\n\u0647\u0630\u0627 \u0627\u0644\u062d\u0633\u0627\u0628 \u0633\u064a\u064f\u0633\u062a\u062e\u062f\u0645 \u0644\u062a\u0645\u062f\u064a\u062f \u0645\u062f\u0629 \u0627\u0644\u062d\u062c\u0632.\n\u0627\u0631\u0633\u0644 \u0627\u0644\u0640 `Bearer Token`.",
        builder.as_markup(),
    )
    await state.set_state(SniperStates.waiting_for_token)
    await callback.answer()

# •••••••••••••••••••••••••••••••••••••••••••
# TASKS PANEL (with post-grab options)
# •••••••••••••••••••••••••••••••••••••••••••

async def list_tasks(callback: types.CallbackQuery):
    async with AsyncSessionLocal() as db:
        repo = UserPrefsRepository(db)
        prefs = await repo.get_global_prefs(callback.from_user.id)
        lang = prefs.language or "ar"

        res_repo = ReservationRepository(db)
        tasks = await res_repo.get_active_tasks(user_id=callback.from_user.id)
        text = (
            f"📊 <b>{i18n.t('active_operations', lang)}:</b>\n"
            "──────────────────\n"
        )
        if not tasks:
            text += f"<i>{i18n.t('no_active_ops', lang)}</i>\n"
        for t in tasks:
            icon, en_label, ar_label = TASK_STATUS_LABELS.get(t.status, ("⚡", t.status, t.status))
            status_label = en_label if lang == "en" else ar_label
            
            hold_info = ""
            if t.hold_expires_at:
                remaining = (t.hold_expires_at - datetime.now(timezone.utc)).total_seconds()
                if remaining > 0:
                    hold_info = f" | ⏳ {int(remaining)}s"
            text += f"{icon} <code>#{t.id}</code> | {status_label} | {t.event_slug}{hold_info}\n"

    builder = InlineKeyboardBuilder()
    for t in tasks[:10]:
        builder.row(types.InlineKeyboardButton(
            text=f"#{t.id} {t.event_slug}",
            callback_data=f"task_detail:{t.id}"
        ))
    builder.row(types.InlineKeyboardButton(text="🔙 عودة", callback_data="back_main"))
    await safe_edit_text(callback.message, text, builder.as_markup())
    await callback.answer()

async def handle_task_detail(callback: types.CallbackQuery):
    """Post-grab options: payment link, extend hold, transfer."""
    task_id = int(callback.data.split(":")[1])
    async with AsyncSessionLocal() as db:
        from database.models.reservation import ReservationTask
        task = await db.get(ReservationTask, task_id)
        if not task:
            await callback.answer("\u0627\u0644\u0645\u0647\u0645\u0629 \u063a\u064a\u0631 \u0645\u0648\u062c\u0648\u062f\u0629")
            return
        acc = await db.get(AuthSession, task.account_id) if task.account_id else None

    hold_info = ""
    if task.hold_expires_at:
        remaining = (task.hold_expires_at - datetime.now(timezone.utc)).total_seconds()
        hold_info = f"\nÃƒÆ’Ã‚Â¢Ãƒâ€šÃ‚ÂÃƒâ€šÃ‚Â° \u0645\u062a\u0628\u0642\u064a: {int(remaining)}s" if remaining > 0 else "\n\U0001f480 \u0645\u0646\u062a\u0647\u064a"

    text = (
        f"\U0001f4cb **\u062a\u0641\u0627\u0635\u064a\u0644 \u0627\u0644\u0645\u0647\u0645\u0629 #{task.id}**\n"
        f"••••••••••••••••••\n"
        f"\U0001f3ad \u0627\u0644\u0641\u0639\u0627\u0644\u064a\u0629: {task.event_slug}\n"
        f"\U0001f4ca \u0627\u0644\u062d\u0627\u0644\u0629: {task.status}\n"
        f"\U0001f3ab \u0627\u0644\u0639\u062f\u062f: {task.seat_count}\n"
        f"\U0001f464 \u0627\u0644\u062d\u0633\u0627\u0628: {acc.email if acc else '--'}\n"
        f"\U0001f511 Hold Token: `{(task.hold_token or '')[:20]}...`\n"
        f"\U0001f504 \u0639\u062f\u062f \u0627\u0644\u062a\u0645\u062f\u064a\u062f\u0627\u062a: {task.retry_count}{hold_info}\n"
    )

    builder = InlineKeyboardBuilder()
    if task.status == "HOLDING":
        builder.row(types.InlineKeyboardButton(text="ÃƒÆ’Ã‚Â¢Ãƒâ€šÃ‚ÂÃƒâ€šÃ‚Â° \u062a\u0645\u062f\u064a\u062f \u0627\u0644\u062d\u062c\u0632 (Swap)", callback_data=f"extend_hold:{task.id}"))
        builder.row(types.InlineKeyboardButton(text="\U0001f4b3 \u0631\u0627\u0628\u0637 \u0627\u0644\u062f\u0641\u0639", callback_data=f"payment_link:{task.id}"))
        builder.row(types.InlineKeyboardButton(text="\U0001f4e4 \u0646\u0642\u0644 \u0644\u062d\u0633\u0627\u0628 \u0627\u062e\u0631", callback_data=f"transfer_hold:{task.id}"))
    builder.row(types.InlineKeyboardButton(text="\u274c \u0627\u0644\u063a\u0627\u0621 \u0627\u0644\u0645\u0647\u0645\u0629", callback_data=f"cancel_task:{task.id}"))
    builder.row(types.InlineKeyboardButton(text="\U0001f519 \u0639\u0648\u062f\u0629", callback_data="list_tasks"))
    await safe_edit_text(callback.message, text, builder.as_markup())
    await callback.answer()

async def handle_extend_hold(callback: types.CallbackQuery):
    """Manual hold extension via smooth swap."""
    task_id = int(callback.data.split(":")[1])
    builder_load = InlineKeyboardBuilder()
    builder_load.row(types.InlineKeyboardButton(text="\U0001f519 \u0625\u0644\u063a\u0627\u0621", callback_data=f"task_detail:{task_id}"))
    await safe_edit_text(
        callback.message,
        "\U0001f504 **\u062c\u0627\u0631\u064a \u062a\u0645\u062f\u064a\u062f \u0627\u0644\u062d\u062c\u0632...**\n_\u0646\u0642\u0644 \u0627\u0644\u062a\u0630\u0627\u0643\u0631 \u0644\u062d\u0633\u0627\u0628 \u062c\u062f\u064a\u062f..._",
        builder_load.as_markup(),
    )
    from services.reservation.swapper import HoldSwapper
    async with AsyncSessionLocal() as db:
        swapper = HoldSwapper(db)
        await swapper.manual_extend(task_id)

# •••••••••••••••••••••••••••••••••••••••••••
# SETTINGS PANEL
# •••••••••••••••••••••••••••••••••••••••••••

async def handle_custom_events_menu(callback: types.CallbackQuery):
    async with AsyncSessionLocal() as db:
        repo = UserPrefsRepository(db)
        p = await repo.get_global_prefs(callback.from_user.id)
        lang = p.language or "ar"

    builder = InlineKeyboardBuilder()
    def t(val): return "✅" if val else "❌"
    
    builder.row(types.InlineKeyboardButton(text=f"{t(p.all_notifications)} تفعيل/تعطيل جميع الاشعارات", callback_data="toggle_pref:all_notifications"))
    builder.row(
        types.InlineKeyboardButton(text=f"{t(p.update_alerts)} التحديثات", callback_data="toggle_pref:update_alerts"),
        types.InlineKeyboardButton(text=f"{t(p.new_event_alerts)} فعاليات جديدة", callback_data="toggle_pref:new_event_alerts")
    )
    builder.row(
        types.InlineKeyboardButton(text=f"{t(p.ticket_change_alerts)} التذاكر", callback_data="toggle_pref:ticket_change_alerts"),
        types.InlineKeyboardButton(text=f"{t(p.price_change_alerts)} الاسعار", callback_data="toggle_pref:price_change_alerts")
    )
    
    builder.row(types.InlineKeyboardButton(text="🎯 تفضيلات الفعاليات", callback_data="event_prefs"))
    builder.row(
        types.InlineKeyboardButton(text="📋 الفئات", callback_data="filter_list:favorite_categories"),
        types.InlineKeyboardButton(text="🏙 المناطق", callback_data="filter_list:favorite_zones")
    )
    
    lang_text = "🇺🇸 English" if lang == "ar" else "🇸🇦 العربية"
    builder.row(types.InlineKeyboardButton(text=f"🌐 {lang_text}", callback_data="toggle_language"))
    
    builder.row(types.InlineKeyboardButton(text="🔙 عودة", callback_data="back_main"))
    await safe_edit_text(callback.message, "⚙️ <b>مركز التحكم والاعدادات</b>", reply_markup=builder.as_markup())
    await callback.answer()

async def handle_toggle_language(callback: types.CallbackQuery):
    async with AsyncSessionLocal() as db:
        repo = UserPrefsRepository(db)
        p = await repo.get_global_prefs(callback.from_user.id)
        new_lang = "en" if p.language == "ar" else "ar"
        await repo.update_global_setting(callback.from_user.id, "language", new_lang)
    await handle_custom_events_menu(callback)

async def handle_filter_list(callback: types.CallbackQuery):
    """Sub-menu for picking favorite/filtered categories or zones."""
    field = callback.data.split(":")[1]
    async with AsyncSessionLocal() as db:
        repo = UserPrefsRepository(db)
        p = await repo.get_global_prefs(callback.from_user.id)
        current = getattr(p, field) or []
        builder = InlineKeyboardBuilder()
        
        if "categories" in field:
            # Common Webook Ticket Categories
            items = [
                ("\U0001f48e VIP", "VIP"), ("\U0001f3c5 Gold", "Gold"), ("\U0001f948 Silver", "Silver"), 
                ("\U0001f949 Bronze", "Bronze"), ("\U0001f3ab CAT 1", "CAT 1"), ("\U0001f3ab CAT 2", "CAT 2"),
                ("\U0001f3ab CAT 3", "CAT 3"), ("\U0001f451 VVIP", "VVIP"), ("\U0001f39f General", "General")
            ]
            for label, slug in items:
                s = "\u2705" if slug in current else "\u274c"
                builder.row(types.InlineKeyboardButton(text=f"{s} {label}", callback_data=f"toggle_item:{field}:{slug}"))
        else:
            # Real Venues from DB
            stmt = select(LiveEvent.venue_name).distinct().where(LiveEvent.venue_name != None)
            venues = (await db.execute(stmt)).scalars().all()
            for v in venues[:20]: # Limit for UI
                s = "\u2705" if v in current else "\u274c"
                builder.row(types.InlineKeyboardButton(text=f"{s} {v}", callback_data=f"toggle_item:{field}:{v}"))
        
        builder.row(types.InlineKeyboardButton(text="\U0001f519 \u062d\u0641\u0638 \u0648\u0639\u0648\u062f\u0629", callback_data="custom_events_menu"))
        await safe_edit_text(
            callback.message,
            f"\U0001f4dd **\u0625\u062f\u0627\u0631\u0629 {field.replace('_',' ')}:**\n\u0627\u062e\u062a\u0631 \u0627\u0644\u0639\u0646\u0627\u0635\u0631 \u0644\u062a\u0641\u0639\u064a\u0644\u0647\u0627 \u0623\u0648 \u062a\u0639\u0637\u064a\u0644\u0647\u0627:",
            builder.as_markup(),
        )
    await callback.answer()

async def handle_toggle_item(callback: types.CallbackQuery):
    _, field, item = callback.data.split(":")
    async with AsyncSessionLocal() as db:
        repo = UserPrefsRepository(db)
        await repo.toggle_list_item(callback.from_user.id, field, item)
    await handle_filter_list(callback)

async def handle_toggle_global_pref(callback: types.CallbackQuery):
    field = callback.data.split(":")[1]
    async with AsyncSessionLocal() as db:
        repo = UserPrefsRepository(db)
        p = await repo.get_global_prefs(callback.from_user.id)
        await repo.update_global_setting(callback.from_user.id, field, not getattr(p, field))
    await handle_custom_events_menu(callback)

async def handle_prompt_reminder(callback: types.CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="\U0001f519 \u0639\u0648\u062f\u0629", callback_data="custom_events_menu"))
    await safe_edit_text(callback.message, "ÃƒÆ’Ã‚Â¢Ãƒâ€šÃ‚Â Ãƒâ€šÃ‚Â° **\u0627\u062f\u062e\u0644 \u0648\u0642\u062a \u0627\u0644\u062a\u0630\u0643\u064a\u0631 \u0628\u0627\u0644\u0633\u0627\u0639\u0627\u062a:**", reply_markup=builder.as_markup())
    await safe_edit_text(callback.message, "ÃƒÆ’Ã‚Â¢Ãƒâ€šÃ‚Â Ãƒâ€šÃ‚Â° **\u0627\u062f\u062e\u0644 \u0648\u0642\u062a \u0627\u0644\u062a\u0630\u0643\u064a\u0631 \u0628\u0627\u0644\u0633\u0627\u0639\u0627\u062a:**", reply_markup=builder.as_markup())
    await state.set_state(SniperStates.waiting_for_reminder_hours)
    await callback.answer()

async def handle_set_reminder(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await safe_answer_text(message, "\u274c \u064a\u0631\u062c\u0649 \u0627\u062f\u062e\u0627\u0644 \u0631\u0642\u0645 \u0635\u062d\u064a\u062d.")
        return
    async with AsyncSessionLocal() as db:
        repo = UserPrefsRepository(db)
        await repo.update_global_setting(message.from_user.id, "reminder_default_hours", int(message.text))
    await safe_answer_text(message, f"\u2705 \u062a\u0645 \u0627\u0644\u062a\u062d\u062f\u064a\u062b \u0627\u0644\u0649 {message.text} \u0633\u0627\u0639\u0629.")
    await state.clear()
    await handle_start(message)

async def handle_sync_now(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="\U0001f519 \u0625\u0644\u063a\u0627\u0621 \u0648\u0627\u0644\u0639\u0648\u062f\u0629", callback_data="back_main"))
    await safe_edit_text(
        callback.message,
        "\U0001f504 **\u062c\u0627\u0631\u064a \u0627\u0644\u0645\u0632\u0627\u0645\u0646\u0629 \u0645\u0639 Webook...**\n_\u064a\u0631\u062c\u0649 \u0627\u0644\u0627\u0646\u062a\u0638\u0627\u0631..._",
        builder.as_markup(),
    )
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="\U0001f519 \u0639\u0648\u062f\u0629", callback_data="back_main"))
    try:
        count = await discovery.sync_all()
        await safe_edit_text(callback.message, 
            f"\u2705 **\u062a\u0645 \u0627\u0644\u0645\u0632\u0627\u0645\u0646\u0629!** {count} \u0641\u0639\u0627\u0644\u064a\u0629 \u062a\u0645 \u062a\u062d\u062f\u064a\u062b\u0647\u0627.",
            reply_markup=builder.as_markup()
        )
    except Exception as e:
        await safe_edit_text(
            callback.message,
            f"\u274c \u0641\u0634\u0644: `{str(e)}`",
            builder.as_markup(),
        )
    await callback.answer()

async def handle_link_account_prompt(callback: types.CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="\U0001f519 \u0639\u0648\u062f\u0629", callback_data="back_main"))
    await safe_edit_text(
        callback.message,
        "\U0001f517 **\u0631\u0628\u0637 \u062d\u0633\u0627\u0628 Webook:**\n"
        "\u064a\u0631\u062c\u0649 \u0627\u0631\u0633\u0627\u0644 \u0627\u0644\u0640 `Bearer Token` \u0627\u0644\u062e\u0627\u0635 \u0628\u062d\u0633\u0627\u0628\u0643.\n"
        "(Network Tab -> api.webook.com -> Headers -> Authorization)",
        builder.as_markup(),
    )
    await state.set_state(SniperStates.waiting_for_token)
    await callback.answer()

async def handle_token_submission(message: types.Message, state: FSMContext):
    token = message.text.replace("Bearer ", "").strip()
    await safe_answer_text(message, "🔄 **جاري التحقق من التوكن...**")

    # Get role from state (set by link_sniper or link_extension)
    data = await state.get_data()
    role = data.get("link_role", "SNIPER")

    from services.account.manager import AccountManager
    async with AsyncSessionLocal() as db:
        mgr = AccountManager(db)
        result = await mgr.add_account_via_token(token, role=role)

    if result.get("error"):
        await safe_answer_text(message, f"❌ {result['error']}")
    else:
        profile = result.get("profile", {})
        name = profile.get("first_name", "")
        email = result.get("email", "")
        role_ar = {"SNIPER": "قنص", "EXTENSION": "تمديد", "MONITOR": "مراقبة"}.get(role, role)
        
        # Check for AUTH_REQUIRED tasks to resume
        async with AsyncSessionLocal() as db:
            from database.models.reservation import ReservationTask, TaskStatus
            stmt = select(ReservationTask).where(
                ReservationTask.user_id == message.from_user.id,
                ReservationTask.status == TaskStatus.AUTH_REQUIRED.value
            ).order_by(ReservationTask.updated_at.desc())
            pending = (await db.execute(stmt)).scalars().first()
            
            resume_builder = InlineKeyboardBuilder()
            resume_text = ""
            if pending:
                resume_builder.row(types.InlineKeyboardButton(
                    text=f"🚀 استئناف المهمة #{pending.id}", 
                    callback_data=f"exec_b:{pending.id}"
                ))
                resume_text = f"\n\n💡 <b>لديك مهمة معلقة:</b> #{pending.id}\nيمكنك الضغط على الزر أدناه لاستئناف القنص فوراً."

            await safe_answer_text(message, 
                f"✅ <b>تم ربط الحساب!</b>\n"
                f"👤 {name} ({email})\n"
                f"🏷️ الدور: {role_ar}{resume_text}",
                reply_markup=resume_builder.as_markup() if pending else None
            )
            
    await state.clear()
    if not result.get("status") in ["created", "updated"]:
         await handle_start(message)
async def handle_speed_book(callback: types.CallbackQuery, state: FSMContext):
    """Speed book: auto-fetches tickets, picks cheapest, asks count only."""
    slug = await resolve_event_slug(callback.data.split(":", 1)[1])
    started = time.perf_counter()
    logger.info(f"[QUICK_RESERVE_START] raw={callback.data} slug={slug} user_id={callback.from_user.id}")

# Validate accounts first
    async with AsyncSessionLocal() as db:
        acc_repo = AccountRepository(db)
        account = await acc_repo.get_sniper_account()
        logger.info(
            f"[QUICK_RESERVE_ACCOUNT_CHECK] slug={slug} ok={bool(account)} "
            f"account_id={account.id if account else None} health={account.health if account else None} "
            f"is_active={account.is_active if account else None}"
        )
        if not account:
            builder = InlineKeyboardBuilder()
            builder.row(types.InlineKeyboardButton(text="\U0001f517 \u0631\u0628\u0637 \u062d\u0633\u0627\u0628 Webook", callback_data="link_account_prompt"))
            builder.row(types.InlineKeyboardButton(text="\U0001f519 عودة", callback_data=f"e_det:{slug}"))
            logger.error(f"[QUICK_RESERVE_NO_ACCOUNT] slug={slug} user_id={callback.from_user.id}")
            await safe_send_media(
                callback,
                "\u26a0  <b>\u0644\u0627 \u064a\u0645\u0643\u0646 \u0627\u0644\u062d\u062c\u0632 \u0628\u062f\u0648\u0646 \u062d\u0633\u0627\u0628 \u0646\u0634\u0637</b>\n\u0627\u0631\u0628\u0637 \u062d\u0633\u0627\u0628 Webook \u0623\u0648 \u0623\u0639\u062f \u062a\u0633\u062c\u064a\u0644 \u0627\u0644\u062f\u062e\u0648\u0644 \u0623\u0648\u0644\u0627\u064b.",
                builder.as_markup()
            )
            await callback.answer()
            return

    logger.info(f"[QUICK_RESERVE_TICKETS_FETCH] slug={slug}")
    tickets_data = await discovery.get_event_tickets_live(slug)
    tickets = extract_ticket_list(tickets_data)

    if not tickets:
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="\U0001f519 عودة", callback_data=f"e_det:{slug}"))
        logger.warning(f"[QUICK_RESERVE_NO_TICKETS] slug={slug} response={str(tickets_data)[:500]}")
        await safe_send_media(callback, "\u26a0  \u0644\u0627 \u062a\u0648\u062c\u062f \u062a\u0630\u0627\u0643\u0631 \u0645\u062a\u0627\u062d\u0629.", builder.as_markup())
        await callback.answer()
        return

    # Auto-sort by price (cheapest live ticket with inventory first)
    active_tickets = [t for t in tickets if ticket_has_available_inventory(t)]
    if not active_tickets:
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="\U0001f519 عودة", callback_data=f"e_det:{slug}"))
        logger.warning(f"[QUICK_RESERVE_NO_INVENTORY] slug={slug} tickets={len(tickets)}")
        await safe_send_media(callback, "\u26a0  لا توجد تذاكر متاحة للحجز حالياً.", builder.as_markup())
        await callback.answer()
        return

    sorted_tickets = sorted(active_tickets, key=lambda x: float(x.get("price") or x.get("base_price") or 9999))
    best = sorted_tickets[0]
    best_name = best.get("title") or best.get("name") or "\u0627\u0641\u0636\u0644 \u0633\u0639\u0631"
    best_price_raw = best.get("price") or best.get("base_price") or "?"
    best_price = format_price_sar(best_price_raw)
    best_id = best.get("_id") or best.get("id") or "0"
    await state.clear()
    best_snapshot = build_ticket_snapshot(best)
    await state.update_data(
        slug=slug,
        ticket_id=best_id,
        ticket_snapshot=best_snapshot,
        ticket_snapshots={str(best_id): best_snapshot},
    )
    await state.set_state(SniperStates.choosing_quantity)
    logger.info(
        f"[QUICK_RESERVE_TICKET_SELECTED] slug={slug} ticket_id={best_id} "
        f"name={best_name} price={best_price} ticket_count={len(tickets)} took={elapsed_ms(started)}ms"
    )

    remaining = best.get("remaining") or best.get("available") or 0
    try:
        remaining = int(remaining)
        avail_text = f" ({remaining} \u0645\u062a\u0627\u062d\u0629)" if remaining > 0 else " (\u0645\u062d\u062f\u0648\u062f)"
    except (ValueError, TypeError):
        avail_text = ""

    text = (
        f"\u26a1 <b>\u0627\u0644\u062d\u062c\u0632 \u0627\u0644\u0633\u0631\u064a\u0639</b>\n"
        f"\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n"
        f"\U0001f7e2 \u062a\u0645 \u0627\u062e\u062a\u064a\u0627\u0631: <b>{clean_html(best_name)}</b>\n"
        f"\U0001f4b0 \u0627\u0644\u0633\u0639\u0631: {best_price} SAR{avail_text}\n\n"
        f"\U0001f522 \u0643\u0645 \u062a\u0630\u0643\u0631\u0629 \u062a\u0631\u064a\u062f\u061f"
    )
    builder = InlineKeyboardBuilder()
    for i in range(1, 6):
        builder.button(text=str(i), callback_data=f"set_q:{i}")
    builder.adjust(3)
    builder.row(types.InlineKeyboardButton(text="\U0001f519 \u0639\u0648\u062f\u0629", callback_data=f"e_det:{slug}"))
    await safe_send_media(callback, text, builder.as_markup())
    await callback.answer()

# • • • • • • • • • • • • • • • • • • • • • • • • • • • • • • • • • • • • • • • • • • • 
# RESALE CHECK — secondary market tickets
# • • • • • • • • • • • • • • • • • • • • • • • • • • • • • • • • • • • • • • • • • • • 

async def handle_resale_check(callback: types.CallbackQuery):
    slug = callback.data.split(":")[1]
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="\U0001f519 \u0625\u0644\u063a\u0627\u0621 \u0648\u0627\u0644\u0639\u0648\u062f\u0629", callback_data=f"event_detail:{slug}"))
    await safe_edit_text(callback.message, "\U0001f504 _\u062c\u0627\u0631\u064a \u0627\u0644\u0628\u062d\u062b \u0641\u064a \u0633\u0648\u0642 \u0627\u0639\u0627\u062f\u0629 \u0627\u0644\u0628\u064a\u0639..._", reply_markup=builder.as_markup())
    from modules.webook.client import WebookApiClient
    api = WebookApiClient()
    resale = await api.get_resale_listing(slug)
    builder = InlineKeyboardBuilder()
    if resale:
        text = f"\U0001f4b1 **\u062a\u0630\u0627\u0643\u0631 \u0627\u0639\u0627\u062f\u0629 \u0627\u0644\u0628\u064a\u0639 ({len(resale)}):**\nÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬\n"
        for r in resale[:10]:
            r_name = r.get("title") or r.get("ticket_title") or "\u062a\u0630\u0643\u0631\u0629"
            r_price = format_price_sar(r.get("price"))
            r_qty = r.get("quantity") or 1
            text += f"ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ {r_name}: {r_price} SAR (x{r_qty})\n"
    else:
        text = "\u26a0 \u0644\u0627 \u062a\u0648\u062c\u062f \u062a\u0630\u0627\u0643\u0631 \u0641\u064a \u0633\u0648\u0642 \u0627\u0639\u0627\u062f\u0629 \u0627\u0644\u0628\u064a\u0639 \u0644\u0647\u0630\u0647 \u0627\u0644\u0641\u0639\u0627\u0644\u064a\u0629."
    builder.row(types.InlineKeyboardButton(text="\U0001f519 \u0639\u0648\u062f\u0629", callback_data=f"event_detail:{slug}"))
    await safe_edit_text(callback.message, text, reply_markup=builder.as_markup())
    await callback.answer()

# •••••••••••••••••••••••••••••••••••••••••••
# BLACKLIST CHECK
# •••••••••••••••••••••••••••••••••••••••••••

async def handle_blacklist_check(callback: types.CallbackQuery):
    slug = callback.data.split(":")[1]
    from modules.webook.client import WebookApiClient
    api = WebookApiClient()
    result = await api.check_blacklist(slug)
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="\U0001f519 \u0639\u0648\u062f\u0629", callback_data=f"event_detail:{slug}"))
    if result and result.get("is_blacklisted"):
        await safe_edit_text(callback.message, "\U0001f6ab **\u0645\u062d\u0638\u0648\u0631:** \u062d\u0633\u0627\u0628\u0643 \u0641\u064a \u0627\u0644\u0642\u0627\u0626\u0645\u0629 \u0627\u0644\u0633\u0648\u062f\u0627\u0621 \u0644\u0647\u0630\u0647 \u0627\u0644\u0641\u0639\u0627\u0644\u064a\u0629.", reply_markup=builder.as_markup())
    else:
        await safe_edit_text(callback.message, "\u2705 **\u0645\u0624\u0647\u0644:** \u0644\u0627 \u064a\u0648\u062c\u062f \u062d\u0638\u0631 \u0639\u0644\u0649 \u062d\u0633\u0627\u0628\u0643 \u0644\u0647\u0630\u0647 \u0627\u0644\u0641\u0639\u0627\u0644\u064a\u0629.", reply_markup=builder.as_markup())
    await callback.answer()

# •••••••••••••••••••••••••••••••••••••••••••
# SUBSCRIBE BY SLUG (from event detail page)
# •••••••••••••••••••••••••••••••••••••••••••

async def handle_sub_add_slug(callback: types.CallbackQuery):
    slug = await resolve_event_slug(callback.data.split(":", 1)[1])
    async with AsyncSessionLocal() as db:
        stmt = select(LiveEvent).where(LiveEvent.slug == slug)
        event = (await db.execute(stmt)).scalar_one_or_none()
        if not event:
            await callback.answer("\u274c \u0627\u0644\u0641\u0639\u0627\u0644\u064a\u0629 \u063a\u064a\u0631 \u0645\u0648\u062c\u0648\u062f\u0629.")
            return
        repo = UserPrefsRepository(db)
        existing = await repo.get_subscription(callback.from_user.id, str(event.id))
        if existing:
            await callback.answer("\u2705 \u0627\u0646\u062a \u0645\u0634\u062a\u0631\u0643 \u0628\u0627\u0644\u0641\u0639\u0644 \u0641\u064a \u062a\u0646\u0628\u064a\u0647\u0627\u062a \u0647\u0630\u0647 \u0627\u0644\u0641\u0639\u0627\u0644\u064a\u0629.")
            return
        await repo.add_subscription(callback.from_user.id, str(event.id))
    await callback.answer("\u2705 \u062a\u0645 \u0627\u0644\u0627\u0634\u062a\u0631\u0627\u0643 \u0641\u064a \u062a\u0646\u0628\u064a\u0647\u0627\u062a \u0627\u0644\u0641\u0639\u0627\u0644\u064a\u0629!")

# •••••••••••••••••••••••••••••••••••••••••••
# EVENT PREFERENCES PANEL
# •••••••••••••••••••••••••••••••••••••••••••

async def handle_event_prefs(callback: types.CallbackQuery):
    async with AsyncSessionLocal() as db:
        repo = UserPrefsRepository(db)
        p = await repo.get_global_prefs(callback.from_user.id)
        fav_cats = p.favorite_categories or []
        fav_zones = p.favorite_zones or []

    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text=f"\U0001f4cb \u0627\u0644\u0641\u0626\u0627\u062a \u0627\u0644\u0645\u0641\u0636\u0644\u0629 ({len(fav_cats)})", callback_data="filter_list:favorite_categories"))
    builder.row(types.InlineKeyboardButton(text=f"\U0001f3d9 \u0627\u0644\u0645\u0646\u0627\u0637\u0642 \u0627\u0644\u0645\u0641\u0636\u0644\u0629 ({len(fav_zones)})", callback_data="filter_list:favorite_zones"))
    builder.row(types.InlineKeyboardButton(text="\U0001f30d \u062a\u0635\u0641\u064a\u0629 \u0627\u0644\u0641\u0626\u0627\u062a", callback_data="filter_list:filtered_categories"))
    builder.row(types.InlineKeyboardButton(text="\U0001f3af \u062a\u0635\u0641\u064a\u0629 \u0627\u0644\u0645\u0646\u0627\u0637\u0642", callback_data="filter_list:filtered_zones"))
    builder.row(types.InlineKeyboardButton(text="\U0001f519 \u0639\u0648\u062f\u0629", callback_data="custom_events_menu"))
    await safe_edit_text(callback.message, 
        f"\U0001f3af **\u062a\u0641\u0636\u064a\u0644\u0627\u062a \u0627\u0644\u0641\u0639\u0627\u0644\u064a\u0627\u062a:**\n"
        f"\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n"
        f"\U0001f4cb \u0641\u0626\u0627\u062a \u0645\u0641\u0636\u0644\u0629: {len(fav_cats)}\n"
        f"\U0001f3d9 \u0645\u0646\u0627\u0637\u0642 \u0645\u0641\u0636\u0644\u0629: {len(fav_zones)}\n",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

# •••••••••••••••••••••••••••••••••••••••••••
# ALL EVENTS BROWSER
# •••••••••••••••••••••••••••••••••••••••••••

async def handle_all_events(callback: types.CallbackQuery):
    events = await discovery.get_all_events(limit=100)
    builder = InlineKeyboardBuilder()
    if not events:
        builder.row(types.InlineKeyboardButton(text="\U0001f504 \u062a\u062d\u062f\u064a\u062b", callback_data="sync_now"))
        builder.row(types.InlineKeyboardButton(text="\U0001f519 \u0639\u0648\u062f\u0629", callback_data="back_main"))
        await safe_edit_text(callback.message, "\u26a0 \u0644\u0627 \u062a\u0648\u062c\u062f \u0641\u0639\u0627\u0644\u064a\u0627\u062a.", reply_markup=builder.as_markup())
        await callback.answer()
        return
    text = f"\U0001f4e1 **\u062c\u0645\u064a\u0639 \u0627\u0644\u0641\u0639\u0627\u0644\u064a\u0627\u062a ({len(events)}):**\n"
    for ev in events:
        d = ev.starts_at.strftime('%m/%d') if ev.starts_at else ''
        s = "\U0001f7e2" if ev.status == "AVAILABLE" else "\U0001f534"
        builder.row(types.InlineKeyboardButton(
            text=f"{s} {ev.title_ar} {d}",
            callback_data=f"e_det:{ev.id}"
        ))
    builder.row(types.InlineKeyboardButton(text="\U0001f519 \u0639\u0648\u062f\u0629", callback_data="back_main"))
    await safe_edit_text(callback.message, text, reply_markup=builder.as_markup())
    await callback.answer()

# •••••••••••••••••••••••••••••••••••••••••••
# TASK ACTIONS (Cancel, Payment, Transfer)
# •••••••••••••••••••••••••••••••••••••••••••

async def handle_cancel_task(callback: types.CallbackQuery):
    task_id = int(callback.data.split(":")[1])
    async with AsyncSessionLocal() as db:
        from database.models.reservation import ReservationTask
        task = await db.get(ReservationTask, task_id)
        if task:
            # ── OPERATIONAL ROBUSTNESS: Cleanly release abandoned holds ──
            if task.hold_token and task.status in ("HOLDING", "PENDING"):
                try:
                    from database.models.account import AuthSession
                    from modules.webook.client import WebookApiClient
                    
                    acc = await db.get(AuthSession, task.account_id) if task.account_id else None
                    if acc and acc.bearer_token:
                        api = WebookApiClient()
                        await api.set_bearer(acc.bearer_token)
                        # Explicitly release to avoid accumulation of abandoned holds
                        await api.release_reservation(slug=task.event_slug, hold_token=task.hold_token)
                except Exception as e:
                    logger.error(f"[CANCEL_TASK] Failed to cleanly release hold_token={task.hold_token}: {e}")
                    
            task.status = "CANCELLED"
            await db.commit()
            
            # Also cancel running async worker task if active
            from services.reservation.worker import ReservationWorker
            if task_id in ReservationWorker._active:
                ReservationWorker._active[task_id].cancel()
                del ReservationWorker._active[task_id]
                
            await callback.answer("✅ تم إلغاء المهمة وتحرير المقاعد بنجاح.")
        else:
            await callback.answer("❌ المهمة غير موجودة.")
    await list_tasks(callback)

async def handle_payment_link(callback: types.CallbackQuery):
    task_id = int(callback.data.split(":")[1])
    async with AsyncSessionLocal() as db:
        from database.models.reservation import ReservationTask
        task = await db.get(ReservationTask, task_id)
        if not task or not task.hold_token:
            await callback.answer("\u274c \u0644\u0627 \u064a\u0648\u062c\u062f \u062d\u062c\u0632 \u0646\u0634\u0637 \u0644\u0647\u0630\u0647 \u0627\u0644\u0645\u0647\u0645\u0629.")
            return
        
        # In a real scenario, we'd generate the webook checkout URL
        payment_url = f"https://webook.com/checkout/{task.hold_token}"
        
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="\U0001f4b3 \u0627\u0630\u0647\u0628 \u0644\u0644\u062f\u0641\u0639", url=payment_url))
    builder.row(types.InlineKeyboardButton(text="\U0001f519 \u0639\u0648\u062f\u0629", callback_data=f"task_detail:{task_id}"))
    
    await safe_edit_text(callback.message, 
        f"\U0001f4b3 **\u0631\u0627\u0628\u0637 \u0627\u0644\u062f\u0641\u0639 \u0644\u0644\u0645\u0647\u0645\u0629 #{task_id}:**\n"
        f"\u064a\u0645\u0643\u0646\u0643 \u0625\u0643\u0645\u0627\u0644 \u0639\u0645\u0644\u064a\u0629 \u0627\u0644\u062f\u0641\u0639 \u0639\u0628\u0631 \u0627\u0644\u0631\u0627\u0628\u0637 \u0627\u0644\u062a\u0627\u0644\u064a:\n\n"
        f"`{payment_url}`",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

async def handle_transfer_hold(callback: types.CallbackQuery):
    task_id = int(callback.data.split(":")[1])
    builder_load = InlineKeyboardBuilder()
    builder_load.row(types.InlineKeyboardButton(text="\U0001f519 \u0625\u0644\u063a\u0627\u0621", callback_data=f"task_detail:{task_id}"))
    await safe_edit_text(callback.message, "\U0001f504 **\u062c\u0627\u0631\u064a \u062a\u0645\u062f\u064a\u062f \u0627\u0644\u062d\u062c\u0632 (Smooth Swap)...**\n_\u064a\u0631\u062c\u0649 \u0627\u0644\u0627\u0646\u062a\u0638\u0627\u0631..._", reply_markup=builder_load.as_markup())
    
    from services.reservation.swapper import HoldSwapper
    async with AsyncSessionLocal() as db:
        swapper = HoldSwapper(db)
        result = await swapper.manual_extend(task_id)
        
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="\U0001f519 \u0639\u0648\u062f\u0629", callback_data=f"task_detail:{task_id}"))
    
    if result.get("status") == "extended":
        await safe_edit_text(callback.message, 
            f"\u2705 **\u062a\u0645 \u0627\u0644\u062a\u0645\u062f\u064a\u062f \u0628\u0646\u062c\u0627\u062d!**\n"
            f"ÃƒÆ’Ã‚Â¢Ãƒâ€šÃ‚ÂÃƒâ€šÃ‚Â° \u064a\u0646\u062a\u0647\u064a: `{result['new_expiry']}`\n"
            f"\U0001f504 \u0639\u062f\u062f \u0627\u0644\u062a\u0645\u062f\u064a\u062f\u0627\u062a: {result['swap_count']}",
            reply_markup=builder.as_markup()
        )
    else:
        await safe_edit_text(callback.message, 
            "\u274c **\u0641\u0634\u0644 \u0627\u0644\u062a\u0645\u062f\u064a\u062f:** " + str(result.get('error', '\u062e\u0637\u0623 \u063a\u064a\u0631 \u0645\u0639\u0631\u0648\u0641')) + ",",
            reply_markup=builder.as_markup()
        )
    await callback.answer()


# Strict detail-flow overrides. These are intentionally defined at the end of
# the module so the dispatcher imports the hardened implementations.

async def handle_show_hold_token(callback: types.CallbackQuery):
    """Show the raw holdtoken so the user can copy/transfer the session."""
    task_id = int(callback.data.split(":")[1])
    async with AsyncSessionLocal() as db:
        from database.models.reservation import ReservationTask
        task = await db.get(ReservationTask, task_id)
        if not task:
            await callback.answer("❌ المهمة غير موجودة")
            return
        acc = await db.get(AuthSession, task.account_id) if task.account_id else None

    token = task.hold_token or ""
    payment_url = None
    for log in reversed(list(task.execution_logs or [])):
        if isinstance(log, dict) and log.get("payment_url"):
            payment_url = log["payment_url"]
            break

    account_label = acc.email if acc else f"#{task.account_id}"
    remaining_s = 0
    if task.hold_expires_at:
        remaining_s = max(0, int((task.hold_expires_at - datetime.now(timezone.utc)).total_seconds()))
    expiry_icon = "✅" if remaining_s > 60 else "⚠️"

    text = (
        f"📤 <b>بيانات نقل الجلسة</b>\n"
        f"──────────────────\n"
        f"🎭 <b>الفعالية:</b> <code>{task.event_slug}</code>\n"
        f"👤 <b>الحساب:</b>  <code>{account_label}</code>\n"
        f"{expiry_icon} <b>الوقت المتبقي:</b> <code>{remaining_s}s</code>\n"
        f"──────────────────\n"
        f"🔑 <b>Hold Token:</b>\n<code>{token}</code>\n"
        f"──────────────────\n"
        f"<i>انسخ الـ Hold Token وأرسله للمستخدم الآخر لإكمال الدفع من حسابه.</i>"
    )

    builder = InlineKeyboardBuilder()
    if payment_url:
        builder.row(types.InlineKeyboardButton(text="🔗 رابط الدفع المباشر", url=payment_url))
    builder.row(
        types.InlineKeyboardButton(text="⏰ تمديد الجلسة", callback_data=f"extend_hold:{task_id}"),
        types.InlineKeyboardButton(text="🔙 عودة", callback_data=f"task_detail:{task_id}"),
    )
    await safe_edit_text(callback.message, text, reply_markup=builder.as_markup())
    await callback.answer()
async def handle_event_detail(callback: types.CallbackQuery, state: FSMContext):
    logger.info(f"[CALLBACK_RECEIVED] {callback.data} | user_id={callback.from_user.id}")
    logger.info("[ROUTER_MATCHED] e_det")
    started = time.perf_counter()
    raw_ref = callback.data.split(":", 1)[1]
    slug = await resolve_event_slug(raw_ref)
    logger.info(f"[DETAIL_START] raw_ref={raw_ref} slug={slug}")
    logger.info(f"[HANDLER_START] handle_event_detail | slug={slug}")
    await state.update_data(slug=slug)

    loading_builder = InlineKeyboardBuilder()
    loading_builder.row(types.InlineKeyboardButton(text="\u0625\u0644\u063a\u0627\u0621 \u0648\u0627\u0644\u0639\u0648\u062f\u0629", callback_data="booking_start"))
    await safe_send_media(callback, "\u062c\u0627\u0631\u064a \u062c\u0644\u0628 \u062a\u0641\u0627\u0635\u064a\u0644 \u0627\u0644\u0641\u0639\u0627\u0644\u064a\u0629...", loading_builder.as_markup())

    db_start = time.perf_counter()
    async with AsyncSessionLocal() as db:
        stmt = select(LiveEvent).where(LiveEvent.slug == slug)
        event = (await db.execute(stmt)).scalar_one_or_none()
        acc_repo = AccountRepository(db)
        account = await acc_repo.get_healthy_account()
        token = account.bearer_token if account else None
    if event:
        logger.info(
            "[DETAIL_DB_LOOKUP] "
            f"id={event.id} slug={event.slug} webook_id={event.webook_id} "
            f"status={event.status} hydration_status={event.hydration_status} "
            f"organization_slug={event_metadata(event).get('organizationSlug') or event_metadata(event).get('organization_id')} "
            f"took={elapsed_ms(db_start)}ms"
        )
    else:
        logger.warning(f"[DETAIL_DB_LOOKUP] slug={slug} result=missing took={elapsed_ms(db_start)}ms")

    cached_detail = event_metadata(event)
    if cached_detail:
        detail, hydration_state = cached_detail, "cache"
        logger.info(f"[DETAIL_HYDRATION_SUCCESS] slug={slug} source=db_cache empty=False took=0ms")
    else:
        detail, hydration_state = await hydrate_detail_with_timeout(slug, bearer_token=token, timeout=15)
    if not detail and event:
        logger.warning(f"[DETAIL_HYDRATION_FAILED] slug={slug} using_db_fallback=true reason={hydration_state}")

    if not detail and not event:
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="\u0639\u0648\u062f\u0629", callback_data="booking_start"))
        await safe_send_media(callback, "\u26a0  \u062a\u0639\u0630\u0631 \u062a\u062d\u0645\u064a\u0644 \u062a\u0641\u0627\u0635\u064a\u0644 \u0627\u0644\u0641\u0639\u0627\u0644\u064a\u0629 \u062d\u0627\u0644\u064a\u0627\u064b", builder.as_markup())
        await callback.answer()
        logger.info(f"[HANDLER_SUCCESS] handle_event_detail unavailable | elapsed_ms={elapsed_ms(started)}")
        return

    parse_start = time.perf_counter()
    logger.info(f"[DETAIL_PARSE_BEGIN] slug={slug}")
    fields = extract_detail_fields(detail, event)
    team_options = extract_team_options(detail, event)
    tickets = detail.get("ticket_packages") or detail.get("event_tickets") or []
    if not tickets:
        tickets_data = await discovery.get_event_tickets_live(slug)
        tickets = extract_ticket_list(tickets_data)
    logger.info(
        f"[DETAIL_PARSE_SUCCESS] slug={slug} venue_present={bool(fields['venue'])} "
        f"date={fields['date_str']} teams={len(team_options)} tickets={len(tickets) if tickets else 0} "
        f"took={elapsed_ms(parse_start)}ms"
    )

    # ── Redesigned Event Card Layout ──
    title_str = clean_html(fields['title'])
    
    text = f"🏆 <b>{title_str}</b>\n"
    if len(team_options) >= 2:
        t1 = clean_html(team_options[0]['name'])
        t2 = clean_html(team_options[1]['name'])
        text += f"<b>{t1} × {t2}</b>\n\n"
    else:
        text += "\n"
        
    if fields['venue']:
        text += f"📍 {clean_html(fields['venue'])}\n"
    if fields['date_str'] and fields['date_str'] not in ('غير محدد', 'N/A', ''):
        text += f"📅 <code>{fields['date_str']}</code>\n"
        
    text += "\n━━━━━━━━━━\n\n"
    
    has_available = False
    if tickets:
        text += f"🎫 <b>التذاكر المتاحة ({len(tickets)}):</b>\n"
        for t in tickets[:8]:
            t_name = clean_html(t.get("title") or t.get("name") or "تذكرة")
            price_val = t.get("price") or t.get("base_price") or 0
            t_price = clean_html(format_price_sar(price_val))
            is_available = ticket_has_available_inventory(t)
            if is_available: has_available = True
            avail_icon = "🟢" if is_available else "🔴"
            text += f"{avail_icon} {t_name} — {t_price} SAR\n"
    else:
        text += "🎫 <b>التذاكر:</b> لم يتم العثور على تذاكر\n"
        
    text += "\n🔄 آخر تحديث: الآن\n"
    if has_available:
        text += "🟢 البيع مفتوح\n"
    elif tickets:
        text += "🔴 مغلق / نفذت التذاكر\n"
    else:
        text += "🟡 بانتظار الطرح\n"
        
    text += "\n━━━━━━━━━━\n"

    if fields["partial"] or hydration_state in ("empty", "timeout", "failed"):
        missing = []
        if not fields['venue']: missing.append("المكان")
        if not fields['date_str'] or fields['date_str'] in ('غير محدد', 'N/A', ''): missing.append("الموعد")
        if missing:
            text += f"\n⚠️ <i>بيانات غير متوفرة: {', '.join(missing)}</i>\n<i>اضغط تحديث لجلب البيانات.</i>\n"

    event_ref = event.id if event else slug
    
    # ── VALIDATION GATE: Compute data health before rendering actions ──
    has_venue = bool(fields['venue'] and fields['venue'] not in ('غير متوفر', 'N/A', ''))
    has_date = bool(fields['date_str'] and fields['date_str'] not in ('غير محدد', 'N/A', ''))
    has_tickets = bool(tickets)
    data_complete = has_venue or has_date  # At least one anchor of trust
    is_partial = fields.get("partial") or hydration_state in ("empty", "timeout", "failed")
    
    builder = InlineKeyboardBuilder()
    
    if data_complete:
        builder.row(types.InlineKeyboardButton(text="🎟 احجز الآن", callback_data=f"b_ev:{event_ref}"))
        builder.row(types.InlineKeyboardButton(text="⚡ حجز سريع", callback_data=f"s_bk:{event_ref}"))
    elif is_partial and has_tickets:
        builder.row(types.InlineKeyboardButton(text="🎟 احجز الآن", callback_data=f"b_ev:{event_ref}"))
    else:
        text += "\n⛔ <b>الحجز غير متاح حالياً</b>\n"
    
    if has_venue:
        builder.row(
            types.InlineKeyboardButton(text="🗺 عرض المخطط", callback_data=f"v_ch:{event_ref}"),
            types.InlineKeyboardButton(text="📡 تتبع التذاكر", callback_data=f"s_ad:{event_ref}")
        )
    else:
        builder.row(
            types.InlineKeyboardButton(text="📡 تتبع التذاكر", callback_data=f"s_ad:{event_ref}")
        )
    
    builder.row(
        types.InlineKeyboardButton(text="🔄 تحديث", callback_data=f"e_det:{event_ref}"),
        types.InlineKeyboardButton(text="↩️ عودة", callback_data="booking_start")
    )

    logger.info(f"[DETAIL_RENDER_BEGIN] slug={slug} image={bool(fields['image_url'])} data_complete={data_complete} has_venue={has_venue} has_date={has_date} has_tickets={has_tickets} callback_ref={event_ref}")
    await safe_send_media(callback, text, builder.as_markup(), image_url=fields["image_url"])
    await callback.answer()
    logger.info(f"[DETAIL_RENDER_SUCCESS] slug={slug} took={elapsed_ms(started)}ms")
    logger.info(f"[HANDLER_SUCCESS] handle_event_detail | elapsed_ms={elapsed_ms(started)}")


async def handle_book_event(callback: types.CallbackQuery, state: FSMContext):
    raw_ref = callback.data.split(":", 1)[1]
    slug = await resolve_event_slug(raw_ref)
    logger.info(f"[UX_TRACE] User clicked Book for slug={slug}")
    await state.clear()
    await state.update_data(slug=slug)

    event = await get_event_by_slug(slug)
    event_ref = str(event.id) if event else raw_ref
    cached_detail = event_metadata(event)
    if cached_detail:
        detail, hydration_state = cached_detail, "cache"
        logger.info(f"[DETAIL_HYDRATION_SUCCESS] slug={slug} source=db_cache empty=False took=0ms")
    else:
        detail, hydration_state = await hydrate_detail_with_timeout(slug, timeout=15)
    if not detail and event:
        logger.warning(f"[DETAIL_HYDRATION_FAILED] slug={slug} booking_uses_db_fallback=true reason={hydration_state}")

    if not detail and not event:
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="عودة", callback_data=f"e_det:{event_ref}"))
        await safe_send_media(callback, "⚠️ تعذر تحميل تفاصيل الفعالية حالياً", builder.as_markup())
        await callback.answer()
        return

    timeslots = detail.get("timeslots") or detail.get("time_slots") or []
    if len(timeslots) > 1:
        await state.set_state(SniperStates.choosing_timeslot)
        builder = InlineKeyboardBuilder()
        for ts in timeslots:
            ts_id = ts.get("id") or ts.get("_id")
            ts_time = ts.get("time") or ts.get("start_at") or ts.get("start_date_time_str") or "Slot"
            builder.row(types.InlineKeyboardButton(text=f"⏰ {ts_time}", callback_data=f"sel_ts:{ts_id}"))
        builder.row(types.InlineKeyboardButton(text="عودة", callback_data=f"e_det:{event_ref}"))
        await safe_send_media(callback, "📅 <b>اختر الموعد المناسب:</b>", builder.as_markup())
        await callback.answer()
        return

    await proceed_to_teams(callback, state, detail, event)


async def proceed_to_teams(callback: types.CallbackQuery, state: FSMContext, detail: dict, event: LiveEvent = None):
    slug = (detail or {}).get("slug") or (event.slug if event else None)
    event_ref = str(event.id) if event else slug
    if not event and slug:
        async with AsyncSessionLocal() as db:
            from database.models.discovery import LiveEvent
            from sqlalchemy import select
            stmt = select(LiveEvent.id).where(LiveEvent.slug == slug)
            db_ev_id = (await db.execute(stmt)).scalar_one_or_none()
            if db_ev_id:
                event_ref = str(db_ev_id)
                
    team_options = extract_team_options(detail, event)
    if len(team_options) >= 2:
        await state.set_state(SniperStates.choosing_team)
        await state.update_data(team_options=team_options)
        builder = InlineKeyboardBuilder()
        for team in team_options:
            builder.row(types.InlineKeyboardButton(text=f"⚽ {team['name']}", callback_data=f"sel_team:{team['id']}"))
        builder.row(types.InlineKeyboardButton(text="أي مكان", callback_data="sel_team:any"))
        builder.row(types.InlineKeyboardButton(text="عودة", callback_data=f"e_det:{event_ref}"))
        logger.info(f"[DETAIL_PARSE_SUCCESS] sports_team_flow slug={slug} teams={team_options}")
        await safe_send_media(callback, "⚽ <b>اختر الفريق المفضل لتحديد منطقة الجلوس:</b>", builder.as_markup())
        await callback.answer()
        return
    await proceed_to_categories(callback, state, slug)


async def proceed_to_categories(callback: types.CallbackQuery, state: FSMContext, slug: str):
    async with AsyncSessionLocal() as db:
        acc_repo = AccountRepository(db)
        # Look up event id to prevent Telegram 64-byte callback_data limits
        from database.models.discovery import LiveEvent
        from sqlalchemy import select
        stmt = select(LiveEvent.id).where(LiveEvent.slug == slug)
        db_ev_id = (await db.execute(stmt)).scalar_one_or_none()
        event_ref = str(db_ev_id) if db_ev_id else slug
        
        accounts = await acc_repo.get_available_accounts()
        if not accounts:
            builder = InlineKeyboardBuilder()
            builder.row(types.InlineKeyboardButton(text="ربط حساب Webook", callback_data="link_account_prompt"))
            builder.row(types.InlineKeyboardButton(text="عودة", callback_data=f"e_det:{event_ref}"))
            await safe_send_media(
                callback,
                "⚠️  <b>لا يمكن الحجز بدون حساب</b>\nيجب ربط حساب Webook أولاً للمتابعة.",
                builder.as_markup()
            )
            await callback.answer()
            return

    tickets_start = time.perf_counter()
    logger.info(f"[API_FETCH] event tickets | slug={slug} timeout=15s")
    try:
        tickets_data = await asyncio.wait_for(discovery.get_event_tickets_live(slug), timeout=15)
        logger.info(f"[API_FETCH] event tickets success | slug={slug} took={elapsed_ms(tickets_start)}ms")
    except asyncio.TimeoutError:
        logger.error(f"[DETAIL_HYDRATION_TIMEOUT] tickets slug={slug} took={elapsed_ms(tickets_start)}ms")
        tickets_data = {}
    except Exception as e:
        logger.error(f"[DETAIL_HYDRATION_FAILED] tickets slug={slug} error={e} took={elapsed_ms(tickets_start)}ms", exc_info=True)
        tickets_data = {}

    # SNIPER FIX: Allow selecting 'Sold Out' categories so they can be sniped/monitored.
    tickets = extract_ticket_list(tickets_data)

    if not tickets:
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="عودة", callback_data=f"e_det:{event_ref}"))
        await safe_send_media(callback, "⚠️  لا توجد فئات متاحة حالياً لهذه الفعالية.", builder.as_markup())
        await callback.answer()
        return

    await state.update_data(ticket_snapshots=build_ticket_snapshot_map(tickets[:15]))
    await state.set_state(SniperStates.choosing_category)
    builder = InlineKeyboardBuilder()
    text = "‏🎫 <b>اختر الفئة (Category/Grade):</b>\n──────────────────\n"
    for i, ticket in enumerate(tickets[:15]):
        default_name = f"فئة {i + 1}"
        t_name = clean_html(ticket.get("title") or ticket.get("name") or default_name)
        t_price = clean_html(format_price_sar(ticket.get("price") or ticket.get("base_price") or "?"))
        t_id = ticket.get("_id") or ticket.get("id") or str(i)
        
        remaining = first_present(ticket.get("remaining"), ticket.get("available"))
        is_available = ticket_has_available_inventory(ticket)
        avail_icon = "🟢" if is_available else "🔴"
        if remaining is None:
            avail_text = ""
        else:
            try:
                avail_num = int(float(remaining))
                avail_text = f" ({avail_num} متاح)" if avail_num > 0 else " (نفذت)"
            except (ValueError, TypeError):
                avail_text = ""
        
        text += f"{avail_icon} {t_name}: {t_price} SAR{avail_text}\n"
        builder.row(types.InlineKeyboardButton(text=f"{avail_icon} {t_name}", callback_data=f"sel_t:{t_id}"))
    builder.row(types.InlineKeyboardButton(text="🔙 عودة", callback_data=f"e_det:{event_ref}"))
    logger.info(f"[UX_TRACE] Sending Category Selection for slug={slug} tickets={len(tickets)}")
    await safe_send_media(callback, text, builder.as_markup())
    await callback.answer()


async def proceed_to_categories(callback: types.CallbackQuery, state: FSMContext, slug: str):
    """
    Override: resilient category loading.
    - primary source: event-ticket-details
    - fallback source: event-detail
    - if no currently available tickets, still show categories with red indicators
    """
    async with AsyncSessionLocal() as db:
        acc_repo = AccountRepository(db)
        # Look up event id to prevent Telegram 64-byte callback_data limits
        from database.models.discovery import LiveEvent
        from sqlalchemy import select
        stmt = select(LiveEvent.id).where(LiveEvent.slug == slug)
        db_ev_id = (await db.execute(stmt)).scalar_one_or_none()
        event_ref = str(db_ev_id) if db_ev_id else slug
        
        accounts = await acc_repo.get_available_accounts()
        if not accounts:
            builder = InlineKeyboardBuilder()
            builder.row(types.InlineKeyboardButton(text="ربط حساب Webook", callback_data="link_account_prompt"))
            builder.row(types.InlineKeyboardButton(text="عودة", callback_data=f"e_det:{event_ref}"))
            await safe_send_media(
                callback,
                "⚠️ <b>لا يمكن الحجز بدون حساب</b>\nيجب ربط حساب Webook أولاً للمتابعة.",
                builder.as_markup(),
            )
            await callback.answer()
            return

    tickets_start = time.perf_counter()
    logger.info(f"[API_FETCH] event tickets | slug={slug} timeout=15s")
    primary_fetch_failed = False
    try:
        tickets_data = await asyncio.wait_for(discovery.get_event_tickets_live(slug), timeout=15)
        logger.info(f"[API_FETCH] event tickets success | slug={slug} took={elapsed_ms(tickets_start)}ms")
    except asyncio.TimeoutError:
        logger.error(f"[DETAIL_HYDRATION_TIMEOUT] tickets slug={slug} took={elapsed_ms(tickets_start)}ms")
        tickets_data = {}
        primary_fetch_failed = True
    except Exception as e:
        logger.error(
            f"[DETAIL_HYDRATION_FAILED] tickets slug={slug} error={e} took={elapsed_ms(tickets_start)}ms",
            exc_info=True,
        )
        tickets_data = {}
        primary_fetch_failed = True

    all_tickets = extract_ticket_list(tickets_data)
    fallback_detail = None

    if not all_tickets:
        logger.warning(f"[TICKET_FETCH_FALLBACK] slug={slug} source=event_detail")
        try:
            detail_data, hydration_state = await hydrate_detail_with_timeout(slug, timeout=12)
            if isinstance(detail_data, dict):
                fallback_detail = detail_data
                all_tickets = (
                    detail_data.get("ticket_packages")
                    or detail_data.get("event_tickets")
                    or detail_data.get("event_ticket")
                    or []
                )
            logger.info(
                f"[TICKET_FETCH_FALLBACK_RESULT] slug={slug} hydration_state={hydration_state} "
                f"tickets={len(all_tickets) if isinstance(all_tickets, list) else 0}"
            )
        except Exception as fallback_err:
            logger.error(f"[TICKET_FETCH_FALLBACK_FAILED] slug={slug} error={fallback_err}", exc_info=True)

    if isinstance(all_tickets, dict):
        all_tickets = [all_tickets]
    if not isinstance(all_tickets, list):
        all_tickets = []

    available_tickets = [ticket for ticket in all_tickets if ticket_has_available_inventory(ticket)]
    
    # HARDENING: If we have available tickets, we ONLY show those.
    # If NO tickets are available, we show all of them but with SOLD OUT markers
    # to avoid the 'Empty Category' confusion.
    tickets = available_tickets
    showing_sold_out_fallback = False
    
    if not tickets and all_tickets:
        tickets = all_tickets
        showing_sold_out_fallback = True

    if not tickets:
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="🔄 تحديث", callback_data=f"b_ev:{event_ref}"))
        builder.row(types.InlineKeyboardButton(text="🔙 عودة", callback_data=f"e_det:{event_ref}"))
        sold_out_hint = False

    if not tickets:
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="عودة", callback_data=f"e_det:{event_ref}"))
        sold_out_hint = False
        if isinstance(fallback_detail, dict):
            sold_out_hint = bool(
                fallback_detail.get("is_soldout")
                or fallback_detail.get("is_sold_out")
                or fallback_detail.get("sold_out")
            )
        if primary_fetch_failed:
            msg = "⚠️ تعذر جلب فئات التذاكر حالياً. جرّب تحديث الصفحة بعد ثواني."
        elif sold_out_hint:
            msg = "🔴 نفدت تذاكر هذه الفعالية حالياً حسب Webook."
        else:
            msg = "⚠️ لا توجد فئات متاحة حالياً لهذه الفعالية."
        await safe_send_media(callback, msg, builder.as_markup())
        await callback.answer()
        return

    await state.update_data(ticket_snapshots=build_ticket_snapshot_map(tickets[:15]))
    await state.set_state(SniperStates.choosing_category)

    builder = InlineKeyboardBuilder()
    text = "‏🎫 <b>اختر الفئة (Category/Grade):</b>\n──────────────────\n"
    if not available_tickets:
        text += "⚠️ الفئات معروضة ولكن غير متاحة الآن حسب بيانات Webook الحالية.\n"

    for i, ticket in enumerate(tickets[:15]):
        default_name = f"فئة {i + 1}"
        t_name = clean_html(ticket.get("title") or ticket.get("name") or default_name)
        t_price = clean_html(format_price_sar(ticket.get("price") or ticket.get("base_price") or "?"))
        t_id = ticket.get("_id") or ticket.get("id") or str(i)

        remaining = first_present(ticket.get("remaining"), ticket.get("available"))
        is_available = ticket_has_available_inventory(ticket)
        avail_icon = "🟢" if is_available else "🔴"
        if remaining is None:
            avail_text = ""
        else:
            try:
                avail_num = int(float(remaining))
                avail_text = f" ({avail_num} متاح)" if avail_num > 0 else " (نفذت)"
            except (ValueError, TypeError):
                avail_text = ""

        text += f"{avail_icon} {t_name}: {t_price} SAR{avail_text}\n"
        builder.row(types.InlineKeyboardButton(text=f"{avail_icon} {t_name}", callback_data=f"sel_t:{t_id}"))

    builder.row(types.InlineKeyboardButton(text="🔙 عودة", callback_data=f"e_det:{event_ref}"))
    logger.info(
        f"[UX_TRACE] Sending Category Selection for slug={slug} tickets={len(tickets)} "
        f"available={len(available_tickets)} primary_fetch_failed={primary_fetch_failed}"
    )
    await safe_send_media(callback, text, builder.as_markup())
    await callback.answer()


def _looks_like_image_url(value: str) -> bool:
    if not isinstance(value, str):
        return False
    lower = value.lower().split("?")[0]
    return lower.startswith("http") and lower.endswith((".png", ".jpg", ".jpeg", ".webp", ".gif"))


def _seatmap_payload(event: LiveEvent, detail: dict = None) -> dict:
    meta = detail if isinstance(detail, dict) and detail else (event.metadata_json or {})
    seats_io = meta.get("seats_io") or meta.get("seatsIo") or meta.get("seats") or {}
    if not isinstance(seats_io, dict):
        seats_io = {}
    venue = meta.get("venue") if isinstance(meta.get("venue"), dict) else {}
    
    static_image = first_present(
        seats_io.get("preview_3_1"),
        seats_io.get("preview_1_1"),
        seats_io.get("preview"),
        seats_io.get("seatmap_image"),
        seats_io.get("stadium_map"),
        meta.get("stadium_image"),
        meta.get("stadiumMap"),
        venue.get("venue_image"),
        venue.get("venue_banner"),
    )
    
    chart_key = event.chart_key or seats_io.get("chart_key") or seats_io.get("chartKey") or seats_io.get("chart_token") or meta.get("chart_key") or meta.get("chartKey")
    event_key = event.event_key or seats_io.get("event_key") or seats_io.get("eventKey") or seats_io.get("event_id") or meta.get("event_key") or meta.get("eventKey")
    workspace_key = event.workspace_key or seats_io.get("workspace_key") or seats_io.get("workspaceKey") or seats_io.get("workspace") or meta.get("workspace_key") or meta.get("workspaceKey")
    provider = event.seats_provider or seats_io.get("provider") or meta.get("seats_provider") or meta.get("seatsProvider")
    
    raw_booking_url = event.interactive_map_url or meta.get("booking_url") or meta.get("bookUrl") or f"https://webook.com/ar/events/{event.slug}"
    if raw_booking_url and "/book" not in raw_booking_url:
        raw_booking_url = raw_booking_url.rstrip("/") + "/book"
    
    return {
        "provider": provider,
        "is_seated": bool(meta.get("is_seated") or meta.get("isSeated") or event_key),
        "static_image": static_image if _looks_like_image_url(static_image) else None,
        "chart_key": chart_key if chart_key and str(chart_key).strip() else None,
        "event_key": event_key if event_key and str(event_key).strip() else None,
        "workspace_key": workspace_key if workspace_key and str(workspace_key).strip() else None,
        "booking_url": raw_booking_url,
    }


async def _seatmap_hold_token(slug: str, event: LiveEvent) -> str | None:
    from modules.webook.client import WebookApiClient

    meta = event_metadata(event)
    event_id = first_present(meta.get("_id"), event.webook_id)
    async with AsyncSessionLocal() as db:
        stmt = (
            select(AuthSession)
            .where(AuthSession.bearer_token.isnot(None))
            .order_by(AuthSession.is_active.desc(), AuthSession.last_used_at.asc().nullsfirst())
            .limit(3)
        )
        accounts = (await db.execute(stmt)).scalars().all()

    logger.info(
        f"[SEATMAP_HOLD_TOKEN_BEGIN] slug={slug} event_id={event_id} candidate_accounts={len(accounts)}"
    )
    for account in accounts:
        client = WebookApiClient(bearer_token=account.bearer_token, proxy=account.proxy_url, account_id=str(account.id))
        data = await client.hold_token(slug=slug, event_id=event_id)
        token = data.get("token") or data.get("holdToken") or data.get("hold_token") if isinstance(data, dict) else None
        if token:
            logger.info(
                f"[SEATMAP_HOLD_TOKEN_SUCCESS] slug={slug} account_id={account.id} "
                f"health={account.health} is_active={account.is_active}"
            )
            return token
        logger.warning(
            f"[SEATMAP_HOLD_TOKEN_FAILED] slug={slug} account_id={account.id} "
            f"health={account.health} response={str(data)[:300]}"
        )
    return None


async def handle_view_chart(callback: types.CallbackQuery):
    started = time.perf_counter()
    raw_ref = callback.data.split(":", 1)[1]
    slug = await resolve_event_slug(raw_ref)
    logger.info(f"[SEATMAP_START] raw_ref={raw_ref} slug={slug}")

    async with AsyncSessionLocal() as db:
        stmt = select(LiveEvent).where(LiveEvent.slug == slug)
        event = (await db.execute(stmt)).scalar_one_or_none()
    logger.info(
        f"[SEATMAP_DB_LOOKUP] slug={slug} found={bool(event)} "
        f"id={event.id if event else None} took={elapsed_ms(started)}ms"
    )

    if not event:
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="\u0639\u0648\u062f\u0629", callback_data="booking_start"))
        await safe_send_media(callback, "\u26a0 \u0644\u0645 \u064a\u062a\u0645 \u0627\u0644\u0639\u062b\u0648\u0631 \u0639\u0644\u0649 \u0627\u0644\u0641\u0639\u0627\u0644\u064a\u0629.", builder.as_markup())
        await callback.answer()
        return

    payload = _seatmap_payload(event)
    logger.info(
        "[SEATMAP_PAYLOAD] "
        f"slug={slug} provider={payload['provider']} is_seated={payload['is_seated']} "
        f"static_image={bool(payload['static_image'])} chart_key={bool(payload['chart_key'])} "
        f"event_key={bool(payload['event_key'])} workspace_key={bool(payload['workspace_key'])}"
    )

    builder = InlineKeyboardBuilder()
    if payload["booking_url"]:
        builder.row(types.InlineKeyboardButton(text="\u0641\u062a\u062d \u0627\u0644\u0645\u062e\u0637\u0637 \u0627\u0644\u062a\u0641\u0627\u0639\u0644\u064a", url=payload["booking_url"]))
    builder.row(types.InlineKeyboardButton(text="\u0639\u0648\u062f\u0629", callback_data=f"e_det:{event.id}"))

    title = clean_html(event.title_ar)
    is_seated_event = bool(payload.get("is_seated"))
    has_chart = bool(payload["chart_key"] and payload["event_key"] and payload["workspace_key"])
    
    # CRITICAL: Seated events must ALWAYS prioritize real stadium chart over static image
    # Only show static_image fallback for non-seated events or when chart rendering fails
    if is_seated_event and has_chart:
        from services.seatmap.renderer import render_seatmap_png

        hold_token = await _seatmap_hold_token(slug, event)
        rendered_path = await render_seatmap_png(
            slug=slug,
            provider=payload["provider"],
            chart_key=payload["chart_key"],
            event_key=payload["event_key"],
            workspace_key=payload["workspace_key"],
            hold_token=hold_token,
        )
        if rendered_path:
            logger.info(f"[SEATMAP_RENDER_SOURCE] slug={slug} source=rendered_png_seated")
            try:
                await callback.message.answer_photo(
                    photo=types.FSInputFile(rendered_path),
                    caption=f"\U0001f5fa <b>\u0645\u062e\u0637\u0637 \u0627\u0644\u0645\u0642\u0627\u0639\u062f</b>\n{title}",
                    parse_mode="HTML",
                    reply_markup=builder.as_markup(),
                )
                await callback.message.delete()
            except Exception as send_error:
                logger.warning(f"[SEATMAP_RENDER_SEND_FAILED] slug={slug} error={send_error}")
                await safe_send_media(
                    callback,
                    f"\U0001f5fa <b>\u062a\u0645 \u062a\u0648\u0644\u064a\u062f \u0627\u0644\u0645\u062e\u0637\u0637</b>\n{title}",
                    builder.as_markup(),
                )
            await callback.answer()
            logger.info(f"[SEATMAP_SENT] slug={slug} mode=seated_chart")
            return
    
    # Non-seated or no chart: use static image if available
    if payload["static_image"]:
        text = f"\U0001f5fa <b>\u0645\u062e\u0637\u0637 \u0627\u0644\u0645\u0642\u0627\u0639\u062f</b>\n{title}"
        logger.info(f"[SEATMAP_RENDER_SOURCE] slug={slug} source=static_image is_seated={is_seated_event}")
        await safe_send_media(callback, text, builder.as_markup(), image_url=payload["static_image"])
        await callback.answer()
        logger.info(f"[SEATMAP_SENT] slug={slug} mode=photo")
        return

    # Fallback: seated with no chart available
    if has_chart:
        from services.seatmap.renderer import render_seatmap_png

        hold_token = await _seatmap_hold_token(slug, event)
        rendered_path = await render_seatmap_png(
            slug=slug,
            provider=payload["provider"],
            chart_key=payload["chart_key"],
            event_key=payload["event_key"],
            workspace_key=payload["workspace_key"],
            hold_token=hold_token,
        )
        if rendered_path:
            logger.info(f"[SEATMAP_RENDER_SOURCE] slug={slug} source=rendered_png path={rendered_path}")
            try:
                await callback.message.answer_photo(
                    photo=types.FSInputFile(rendered_path),
                    caption=f"\U0001f5fa <b>\u0645\u062e\u0637\u0637 \u0627\u0644\u0645\u0642\u0627\u0639\u062f</b>\n{title}",
                    parse_mode="HTML",
                    reply_markup=builder.as_markup(),
                )
                await callback.message.delete()
            except Exception as send_error:
                logger.warning(f"[SEATMAP_RENDER_SEND_FAILED] slug={slug} path={rendered_path} error={send_error}")
                await safe_send_media(
                    callback,
                    f"\U0001f5fa <b>\u062a\u0645 \u062a\u0648\u0644\u064a\u062f \u0645\u062e\u0637\u0637 \u0627\u0644\u0645\u0642\u0627\u0639\u062f</b>\n{title}\n\u0627\u0644\u0645\u0644\u0641 \u0645\u062d\u0641\u0648\u0638 \u0644\u0643\u0646 \u062a\u0639\u0630\u0631 \u0625\u0631\u0633\u0627\u0644\u0647 \u0639\u0628\u0631 Telegram.",
                    builder.as_markup(),
                )
            await callback.answer()
            logger.info(f"[SEATMAP_SENT] slug={slug} mode=rendered_png took={elapsed_ms(started)}ms")
            return

    if payload["booking_url"]:
        logger.info(f"[SEATMAP_RENDER_SOURCE] slug={slug} source=webook_external_fallback provider={payload['provider']}")
        await safe_send_media(
            callback,
            f"\U0001f5fa <b>\u0645\u062e\u0637\u0637 \u0627\u0644\u0645\u0642\u0627\u0639\u062f \u0627\u0644\u062a\u0641\u0627\u0639\u0644\u064a</b>\n{title}\n\n"
            "\u062a\u0639\u0630\u0631 \u062a\u0648\u0644\u064a\u062f \u0635\u0648\u0631\u0629 \u0644\u0644\u0645\u062e\u0637\u0637 \u062f\u0627\u062e\u0644 Telegram \u0641\u064a \u0647\u0630\u0647 \u0627\u0644\u0628\u064a\u0626\u0629. \u0631\u0627\u0628\u0637 Webook \u0638\u0627\u0647\u0631 \u0643\u062d\u0644 \u0627\u062d\u062a\u064a\u0627\u0637\u064a \u0641\u0642\u0637.",
            builder.as_markup()
        )
        await callback.answer()
        logger.info(f"[SEATMAP_SENT] slug={slug} mode=external_url took={elapsed_ms(started)}ms")
        return

    logger.warning(f"[SEATMAP_RENDER_SOURCE] slug={slug} source=missing_visual")
    await safe_send_media(
        callback,
        f"\u26a0 \u0644\u0627 \u064a\u0648\u062c\u062f \u0645\u062e\u0637\u0637 \u0628\u0635\u0631\u064a \u0645\u062a\u0627\u062d \u062d\u0627\u0644\u064a\u0627\u064b \u0644\u0647\u0630\u0647 \u0627\u0644\u0641\u0639\u0627\u0644\u064a\u0629.\n{title}",
        builder.as_markup()
    )
    await callback.answer()
    logger.info(f"[SEATMAP_SENT] slug={slug} mode=unavailable took={elapsed_ms(started)}ms")