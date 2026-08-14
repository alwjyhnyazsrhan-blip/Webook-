import re
from typing import Optional, Dict
from core.logging.logger import logger
from sqlalchemy import select
from database.models.discovery import Genre

class TaxonomyEngine:
    """
    Centralized Hierarchical Taxonomy Derivation Engine.
    Implements a resilience ladder for event categorization.
    """

    # Primary Category to Genre Slug Mapping
    # These are used as grouping buckets in the bot UI
    CATEGORY_MAP = {
        "Sport Event": "sports",
        "Sport Experience": "sports",
        "Music Event": "concerts",
        "Concert": "concerts",
        "Entertainment Event": "entertainment",
        "Entertainment Experience": "entertainment",
        "Theater": "theater",
        "Theater & Performing Arts": "theater",
        "Restaurant": "restaurants",
        "Experience": "experiences",
        "Package": "packages",
        "Zone": "zones",
        "football": "sports",
    }

    # Authoritative Entity Mapping (only for clear matches)
    ENTITY_MAP = {
        "saudi-pro-league": "saudi-pro-league",
        "mdl-beast": "mdl-beast",
        "riyadh-season": "riyadh-season",
        "jeddah-season": "jeddah-season",
        "wwe": "wwe",
        "f1": "formula1-saudi-arabian-grand-prix",
    }

    # Keyword to Genre/Entity Slug Mapping
    KEYWORD_MAP = {
        "rsl": "saudi-pro-league",
        "spl": "saudi-pro-league",
        "mdlbeast": "mdl-beast",
        "soundstorm": "mdl-beast",
        "wwe": "wwe",
        "f1": "f1",
        "formula1": "f1",
        "neom": "neom",
        "roshn": "roshn",
        "alula": "alula",
        "jeddah": "jeddah-season",
        "riyadh": "riyadh-season",
        "diriyah": "diriyah-season",
        "boulevard": "riyadh-season",
        "wonderland": "riyadh-season",
        "winter": "experiences",
        "safari": "experiences",
        "cup": "sports",
        "boxing": "sports",
        "tennis": "sports",
    }

    # Regex Patterns for Entity Detection (more specific now)
    PATTERNS = [
        (re.compile(r"(saudi-pro-league|roshn-saudi-league|rsl|spl)"), "saudi-pro-league"),
        (re.compile(r"(riyadh-season|rs-24|rs24|rs-25|rs25)"), "riyadh-season"),
        (re.compile(r"(mdlbeast|mdl-beast|soundstorm|balad-beast)"), "mdl-beast"),
        (re.compile(r"(wwe|smackdown|raw-|crown-jewel|royal-rumble)"), "wwe"),
        (re.compile(r"(f1|formula[\s-]?1|grand[\s-]?prix)"), "f1"),
        (re.compile(r"(theater|theatre|theatrical|play|musical|\u0645\u0633\u0631\u062d\u064a\u0629)"), "theater"),
        (re.compile(r"(cinema|film|festival|red-sea|movie)"), "cinema"),
        (re.compile(r"(esports|gaming|competitive|playstation|xbox|gamer|ewc|esports-world-cup)"), "esports"),
        (re.compile(r"(restaurant|cafe|dining|food|brunch|lounge|kitchen|chef)"), "restaurants"),
        (re.compile(r"(concert|live-music|singer|gig|performance)"), "concerts"),
    ]

    # Arabic Keyword Map (Entity focus)
    ARABIC_MAP = {
        "\u062f\u0648\u0631\u064a \u0631\u0648\u0634\u0646": "saudi-pro-league",
        "\u0645\u0648\u0633\u0645 \u0627\u0644\u0631\u064a\u0627\u0636": "riyadh-season",
        "\u0645\u0648\u0633\u0645 \u062c\u062f\u0629": "jeddah-season",
        "\u0645\u062f\u0644 \u0628\u064a\u0633\u062a": "mdl-beast",
        "\u0641\u0648\u0631\u0645\u0648\u0644\u0627": "f1",
        "\u0627\u0644\u0647\u0644\u0627\u0644": "al-hilal",
        "\u0627\u0644\u0646\u0635\u0631": "al-nassr",
        "\u0627\u0644\u0627\u062a\u062d\u062f": "al-ittihad",
        "\u0627\u0644\u0623\u0647\u0644\u064a": "al-ahli",
        "\u0645\u0628\u0627\u0631\u0627\u0629": "sports",
        "\u062d\u0641\u0644": "concerts",
        "\u0645\u0633\u0631\u062d": "theater",
    }

    @staticmethod
    def normalize_genre_slug(value: Optional[str]) -> Optional[str]:
        if not value:
            return None
        normalized = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
        return normalized or None

    @classmethod
    async def resolve_genre_id(cls, db, slug: str, title: Optional[str] = None, category: Optional[str] = None, org_slug: Optional[str] = None) -> Optional[int]:
        """
        Main entry point for taxonomy resolution.
        Ladder: ENTITY_DETECTION -> CATEGORY -> ORGANIZATION -> FALLBACK
        """
        genre_slug = cls.resolve_genre_slug(slug, title, category, org_slug)
        if not genre_slug:
            return None

        stmt = select(Genre.id).where(Genre.slug == genre_slug)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    def resolve_genre_slug(cls, slug: str, title: Optional[str] = None, category: Optional[str] = None, org_slug: Optional[str] = None) -> Optional[str]:
        """
        Derives the genre slug using a smarter hierarchical ladder.
        """
        slug_low = slug.lower()
        title_low = title.lower() if title else ""
        canonical_category = category.strip() if isinstance(category, str) else ""
        normalized_category = cls.normalize_genre_slug(canonical_category)

        # 1. CATEGORY MAPPING (Treat upstream Webook category as the primary source of truth)
        if canonical_category and canonical_category in cls.CATEGORY_MAP:
            return cls.CATEGORY_MAP[canonical_category]
        if normalized_category and normalized_category not in ("internal", "unknown", "event"):
            return normalized_category

        # 2. ORGANIZATION FALLBACK (Use organization only when category is unavailable)
        if org_slug and org_slug in cls.ENTITY_MAP:
            return cls.ENTITY_MAP[org_slug]

        # 3. ORGANIZATION AS CATEGORY (Final attempt before 'other')
        # Keep this strict to avoid heuristic/fake categories.
        if org_slug and org_slug not in ("", "webook", "internal"):
            return org_slug

        # 4. DEFAULT FALLBACK
        return "other"

    @classmethod
    def get_all_genre_slugs(cls) -> set:
        """Returns all unique genre slugs used in the taxonomy maps."""
        slugs = set(cls.CATEGORY_MAP.values())
        slugs.update(cls.ENTITY_MAP.values())
        slugs.update(cls.KEYWORD_MAP.values())
        for _, gslug in cls.PATTERNS:
            slugs.add(gslug)
        slugs.update(cls.ARABIC_MAP.values())
        return slugs
