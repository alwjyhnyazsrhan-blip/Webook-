"""
Consumer-Facing Navigation Layer.

This module provides the user-visible browsing hierarchy for the Telegram bot,
decoupled from the raw database genre/taxonomy system.

Design principles:
  1. Categories mirror Webook's actual homepage (Football, Sports, Concerts, etc.)
  2. Football has sub-navigation (Saudi Pro League, individual clubs)
  3. Empty categories are hidden automatically
  4. Events are classified by slug/title pattern matching, NOT by the API's
     unreliable 'type' field
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple
from datetime import datetime, timezone

from sqlalchemy import select, and_, or_, func
from database.models.discovery import LiveEvent
from core.database.postgres import AsyncSessionLocal
from core.logging.logger import logger


# ─── ICON REGISTRY ──────────────────────────────────────────────────────────
CATEGORY_ICONS = {
    "football":     "⚽",
    "sports":       "🏅",
    "concerts":     "🎵",
    "theater":      "🎭",
    "experiences":  "🎪",
    "esports":      "🎮",
    "seasons":      "🌟",
    "motorsport":   "🏎️",
    "other":        "📌",
}

CLUB_ICONS = {
    "al-hilal":     "💙",
    "al-nassr":     "💛",
    "al-ittihad":   "🖤",
    "al-ahli":      "💚",
    "al-shabab":    "⚪",
    "al-ettifaq":   "🟢",
    "al-raed":      "🔴",
    "al-fateh":     "🔵",
    "al-taawoun":   "🟡",
    "al-qadsiah":   "🟠",
    "al-khaleej":   "🟤",
    "al-okhdood":   "🟣",
    "al-kholood":   "⚫",
    "al-hazem":     "🔶",
    "al-riyadh":    "🔷",
    "al-orubah":    "🔸",
    "al-weihda":    "🔹",
    "neom":         "🌊",
}


# ─── CLASSIFICATION RULES ───────────────────────────────────────────────────
# Each rule: (compiled regex for slug OR title_ar, target_nav_category)
# More specific rules come FIRST so they match before generic ones.

_FOOTBALL_SLUG_RE = re.compile(
    r"(rsl[-_]|spl[-_]|saudi-pro-league|roshn|"
    r"al-hilal|al-nassr|al-ittihad|al-ahli|al-shabab|"
    r"al-ettifaq|al-raed|al-fateh|al-taawoun|al-qadsiah|"
    r"al-khaleej|al-okhdood|al-kholood|al-hazem|al-riyadh|"
    r"al-orubah|al-weihda|neom-fc|"
    r"season-package.*al-|"
    r"jawwy-elite-league)",
    re.IGNORECASE,
)

_FOOTBALL_TITLE_RE = re.compile(
    r"(دوري روشن|الدوري السعودي|"
    r"الهلال|النصر|الاتحاد|الأهلي|الشباب|"
    r"الاتفاق|الرائد|الفتح|التعاون|القادسية|"
    r"الخليج|الاخدود|الخلود|الحزم|الرياض|"
    r"نيوم ضد|ضد نادي)",
    re.IGNORECASE,
)

_CONCERT_RE = re.compile(
    r"(حفل|vocally|concert|live-music|singer|"
    r"adam-at-|abdulaziz-|assala-|"
    r"سامي يوسف|جلسة الفنان|كورالا|"
    r"jazzablanca|صوفي|أناشيد|أغاني)",
    re.IGNORECASE,
)

_THEATER_RE = re.compile(
    r"(مسرح|theater|theatre|musical|play-|"
    r"عرض قادم|show-v\d|choralla|improv|"
    r"ارتجال|ليالي|lantidote|incarnation|"
    r"leonphal|animaex|شو دو)",
    re.IGNORECASE,
)

_EXPERIENCE_RE = re.compile(
    r"(experience|workshop|ورشة|معرض|expo|"
    r"فست|fest|collectors|safari|tour|"
    r"جولات|fit-expo|chinese-calligraphy)",
    re.IGNORECASE,
)

_ESPORTS_RE = re.compile(
    r"(esports|gaming|spw[-_]|e-sports|ewc|"
    r"playstation|xbox|gamer|reignited)",
    re.IGNORECASE,
)

_MOTORSPORT_RE = re.compile(
    r"(motogp|formula|f1|grand-prix|racing|"
    r"سباق|فورمولا|saudi-cup)",
    re.IGNORECASE,
)

_SEASON_RE = re.compile(
    r"(riyadh-season|jeddah-season|موسم الرياض|موسم جدة|"
    r"season-package|seasonal-|diamond-.*member|"
    r"mdlbeast|mdl-beast|beast-house|soundstorm|"
    r"boulevard|wonderland)",
    re.IGNORECASE,
)

_SPORTS_RE = re.compile(
    r"(sport|equestrian|polo|فروسية|بولو|"
    r"boxing|tennis|wwe|wrestling|"
    r"smackdown|crown-jewel|royal-rumble)",
    re.IGNORECASE,
)

# Football club slug detection for sub-navigation
_CLUB_SLUG_PATTERNS = [
    (re.compile(r"al-hilal|الهلال"), "al-hilal", "الهلال"),
    (re.compile(r"al-nassr|النصر"), "al-nassr", "النصر"),
    (re.compile(r"al-ittihad|الاتحاد"), "al-ittihad", "الاتحاد"),
    (re.compile(r"al-ahli|الأهلي"), "al-ahli", "الأهلي"),
    (re.compile(r"al-shabab|الشباب"), "al-shabab", "الشباب"),
    (re.compile(r"al-ettifaq|الاتفاق"), "al-ettifaq", "الاتفاق"),
    (re.compile(r"al-qadsiah|القادسية"), "al-qadsiah", "القادسية"),
    (re.compile(r"al-khaleej|الخليج"), "al-khaleej", "الخليج"),
    (re.compile(r"al-okhdood|الاخدود"), "al-okhdood", "الاخدود"),
    (re.compile(r"al-kholood|الخلود"), "al-kholood", "الخلود"),
    (re.compile(r"al-hazem|الحزم"), "al-hazem", "الحزم"),
    (re.compile(r"al-riyadh|الرياض ضد"), "al-riyadh", "الرياض"),
    (re.compile(r"al-fateh|الفتح"), "al-fateh", "الفتح"),
    (re.compile(r"al-taawoun|التعاون"), "al-taawoun", "التعاون"),
    (re.compile(r"al-raed|الرائد"), "al-raed", "الرائد"),
    (re.compile(r"neom|نيوم"), "neom", "نيوم"),
]


# ─── DATA CLASSES ────────────────────────────────────────────────────────────

@dataclass
class NavCategory:
    """A consumer-facing navigation category."""
    key: str                # Internal key (e.g. "football")
    label_ar: str           # Arabic display name
    label_en: str           # English display name
    icon: str               # Emoji
    event_count: int = 0    # Live event count (computed at query time)
    has_subcategories: bool = False


@dataclass
class NavSubCategory:
    """Sub-navigation item (e.g. a football club under Football)."""
    key: str
    label_ar: str
    icon: str
    event_count: int = 0


# ─── CLASSIFICATION ENGINE ──────────────────────────────────────────────────

def classify_event(slug: str, title_ar: str = "", title_en: str = "") -> str:
    """
    Classify an event into a consumer-facing navigation category.
    Returns one of: football, sports, concerts, theater, experiences,
                    esports, seasons, motorsport, other
    """
    search_text = f"{slug} {title_ar} {title_en}".lower()

    # Order matters: most specific first
    if _FOOTBALL_SLUG_RE.search(slug) or _FOOTBALL_TITLE_RE.search(title_ar or ""):
        return "football"
    if _MOTORSPORT_RE.search(search_text):
        return "motorsport"
    if _ESPORTS_RE.search(search_text):
        return "esports"
    if _CONCERT_RE.search(search_text):
        return "concerts"
    if _THEATER_RE.search(search_text):
        return "theater"
    if _EXPERIENCE_RE.search(search_text):
        return "experiences"
    if _SEASON_RE.search(search_text):
        return "seasons"
    if _SPORTS_RE.search(search_text):
        return "sports"

    return "other"


def detect_clubs(slug: str, title_ar: str = "") -> List[str]:
    """Detect which football clubs are involved in an event."""
    clubs = []
    text = f"{slug} {title_ar}"
    for pattern, club_key, _ in _CLUB_SLUG_PATTERNS:
        if pattern.search(text):
            clubs.append(club_key)
    return clubs


# ─── NON-RESERVABLE EVENT FILTER ─────────────────────────────────────────────
# These slug patterns match system/homepage/template entries that the scraper
# picks up from Webook but are NOT bookable events. They must never appear
# in the consumer-facing navigation.
_NON_RESERVABLE_RE = re.compile(
    r"(homepage|^jcsa-|^test-|^demo-|^template-|^placeholder-|"
    r"-homepage$|^webook-home|^staging-|^internal-)",
    re.IGNORECASE,
)

# Title-based filter for entries that look like system/admin records
_NON_RESERVABLE_TITLE_RE = re.compile(
    r"(homepage|test event|placeholder|template|staging|internal)",
    re.IGNORECASE,
)


def is_reservable_event(ev: LiveEvent) -> bool:
    """
    Returns False for events that are system entries, homepages,
    or clearly non-bookable records that leaked from the scraper.
    """
    slug = ev.slug or ""
    title = ev.title_ar or ev.title_en or ""

    # Slug-based exclusion
    if _NON_RESERVABLE_RE.search(slug):
        return False

    # Title-based exclusion
    if _NON_RESERVABLE_TITLE_RE.search(title):
        return False

    # If both title and slug are suspiciously short/empty
    if len(slug) < 3 and len(title) < 3:
        return False

    return True


# ─── QUERY ENGINE ────────────────────────────────────────────────────────────

# Shared filter for "visible" events
_VISIBLE_STATUSES = ["READY", "DISCOVERED", "PARTIAL", "HYDRATING"]
_EXCLUDED_EVENT_STATUSES = ["PAST", "GHOST"]


async def _get_all_live_events() -> List[LiveEvent]:
    """Fetch all currently visible, future, reservable events from DB."""
    async with AsyncSessionLocal() as db:
        now = datetime.now(timezone.utc)
        stmt = (
            select(LiveEvent)
            .where(
                and_(
                    LiveEvent.hydration_status.in_(_VISIBLE_STATUSES),
                    LiveEvent.status.notin_(_EXCLUDED_EVENT_STATUSES),
                    or_(LiveEvent.starts_at == None, LiveEvent.starts_at > now),
                )
            )
            .order_by(LiveEvent.starts_at.asc().nullslast())
        )
        result = await db.execute(stmt)
        all_events = result.scalars().all()

        # Apply consumer-facing filter: exclude non-reservable entries
        reservable = [ev for ev in all_events if is_reservable_event(ev)]
        filtered_count = len(all_events) - len(reservable)
        if filtered_count > 0:
            logger.info(
                f"[NAV_FILTER] Excluded {filtered_count} non-reservable entries "
                f"from {len(all_events)} total events"
            )
        return reservable


async def get_nav_categories() -> List[NavCategory]:
    """
    Build the top-level consumer-facing navigation.
    Only returns categories that have at least 1 live event.
    """
    all_events = await _get_all_live_events()

    # Classify every event
    category_counts: Dict[str, int] = {}
    for ev in all_events:
        cat = classify_event(ev.slug, ev.title_ar or "", ev.title_en or "")
        category_counts[cat] = category_counts.get(cat, 0) + 1

    # Define the display order (mirrors Webook homepage)
    NAV_DEFINITION = [
        ("football",    "كرة القدم",  "Football",     True),
        ("sports",      "رياضة",      "Sports",       False),
        ("concerts",    "حفلات",      "Concerts",     False),
        ("theater",     "عروض ومسرح", "Theater",      False),
        ("experiences", "تجارب",      "Experiences",  False),
        ("esports",     "الرياضات الإلكترونية", "Esports", False),
        ("seasons",     "المواسم",    "Seasons",      False),
        ("motorsport",  "رياضة المحركات", "Motorsport", False),
        ("other",       "أخرى",       "Other",        False),
    ]

    result = []
    for key, label_ar, label_en, has_sub in NAV_DEFINITION:
        count = category_counts.get(key, 0)
        if count == 0:
            continue  # CRITICAL: Hide empty categories
        icon = CATEGORY_ICONS.get(key, "📌")
        result.append(NavCategory(
            key=key,
            label_ar=label_ar,
            label_en=label_en,
            icon=icon,
            event_count=count,
            has_subcategories=has_sub,
        ))

    logger.info(
        f"[NAV] Built {len(result)} visible categories from {len(all_events)} events | "
        f"counts={category_counts}"
    )
    return result


async def get_football_subcategories() -> List[NavSubCategory]:
    """
    Build the Football sub-navigation (clubs + league).
    Only returns clubs that have at least 1 live event.
    """
    all_events = await _get_all_live_events()

    club_counts: Dict[str, int] = {}
    league_count = 0
    for ev in all_events:
        cat = classify_event(ev.slug, ev.title_ar or "", ev.title_en or "")
        if cat != "football":
            continue
        league_count += 1
        clubs = detect_clubs(ev.slug, ev.title_ar or "")
        for club in clubs:
            club_counts[club] = club_counts.get(club, 0) + 1

    result = []
    # Add "All Football" first
    if league_count > 0:
        result.append(NavSubCategory(
            key="all_football",
            label_ar=f"جميع مباريات كرة القدم",
            icon="⚽",
            event_count=league_count,
        ))

    # Add clubs with events
    for pattern, club_key, club_name_ar in _CLUB_SLUG_PATTERNS:
        count = club_counts.get(club_key, 0)
        if count == 0:
            continue
        icon = CLUB_ICONS.get(club_key, "⚽")
        result.append(NavSubCategory(
            key=club_key,
            label_ar=club_name_ar,
            icon=icon,
            event_count=count,
        ))

    return result


async def get_events_for_nav_category(nav_key: str) -> List[LiveEvent]:
    """Get all live events matching a navigation category key."""
    all_events = await _get_all_live_events()
    return [
        ev for ev in all_events
        if classify_event(ev.slug, ev.title_ar or "", ev.title_en or "") == nav_key
    ]


async def get_events_for_club(club_key: str) -> List[LiveEvent]:
    """Get all live football events involving a specific club."""
    all_events = await _get_all_live_events()
    results = []
    for ev in all_events:
        cat = classify_event(ev.slug, ev.title_ar or "", ev.title_en or "")
        if cat != "football":
            continue
        clubs = detect_clubs(ev.slug, ev.title_ar or "")
        if club_key in clubs:
            results.append(ev)
    return results
