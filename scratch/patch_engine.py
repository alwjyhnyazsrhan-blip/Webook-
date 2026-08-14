"""
Patch engine.py:
  Fix 1 - Add _INTERNAL_GENRE_BLACKLIST class var + filter in get_live_categories query
  Fix 2 - Guard _get_or_create_genre against blacklisted slugs/names
  Fix 3 - Guard _upsert_event_shell against using "internal" as genre name
"""
import re

ENGINE_PATH = "services/discovery/engine.py"

with open(ENGINE_PATH, "r", encoding="utf-8") as f:
    src = f.read()

# ── Fix 1a: Insert _INTERNAL_GENRE_BLACKLIST class variable right before get_live_categories
OLD_1 = '''    async def get_live_categories(self) -> list:
        async with AsyncSessionLocal() as db:
            # First try: strictly active genres
            stmt = select(Genre).where(Genre.is_active == True).order_by(Genre.name_ar.asc())
            result = await db.execute(stmt)
            cats = result.scalars().all()'''

NEW_1 = '''    # Webook API internal type labels — never show as user-visible categories
    _INTERNAL_GENRE_BLACKLIST = frozenset({
        "internal", "none", "unknown", "null", "undefined",
    })

    async def get_live_categories(self) -> list:
        async with AsyncSessionLocal() as db:
            # First try: active genres, excluding internal API type labels
            stmt = (
                select(Genre)
                .where(Genre.is_active == True)
                .where(Genre.slug.notin_(self._INTERNAL_GENRE_BLACKLIST))
                .where(Genre.name_ar.notin_(self._INTERNAL_GENRE_BLACKLIST))
                .order_by(Genre.name_ar.asc())
            )
            result = await db.execute(stmt)
            cats = result.scalars().all()'''

assert OLD_1 in src, "Fix 1a: target not found"
src = src.replace(OLD_1, NEW_1, 1)
print("Fix 1a applied: blacklist + get_live_categories filter")

# ── Fix 1b: Also filter the fallback query
OLD_1B = '''                fallback_stmt = (
                    select(Genre)
                    .join(LiveEvent, LiveEvent.genre_id == Genre.id)
                    .where(LiveEvent.status != "GHOST")
                    .where(LiveEvent.hydration_status.in_(["READY", "DISCOVERED", "PARTIAL", "HYDRATING"]))
                    .distinct()
                    .order_by(Genre.name_ar.asc())
                )'''

NEW_1B = '''                fallback_stmt = (
                    select(Genre)
                    .join(LiveEvent, LiveEvent.genre_id == Genre.id)
                    .where(LiveEvent.status != "GHOST")
                    .where(LiveEvent.hydration_status.in_(["READY", "DISCOVERED", "PARTIAL", "HYDRATING"]))
                    .where(Genre.slug.notin_(self._INTERNAL_GENRE_BLACKLIST))
                    .where(Genre.name_ar.notin_(self._INTERNAL_GENRE_BLACKLIST))
                    .distinct()
                    .order_by(Genre.name_ar.asc())
                )'''

if OLD_1B in src:
    src = src.replace(OLD_1B, NEW_1B, 1)
    print("Fix 1b applied: fallback query filter")
else:
    print("Fix 1b: target not found (skipping)")

# ── Fix 2: Harden _get_or_create_genre
OLD_2 = '''    async def _get_or_create_genre(self, db, slug: str, name: str) -> int:
        slug = slug or "other"
        name = name or slug.replace("-", " ").title()
        name_ar, name_en = FRONTEND_CATEGORY_LABELS.get(slug, (name, name))'''

NEW_2 = '''    async def _get_or_create_genre(self, db, slug: str, name: str) -> int:
        slug = (slug or "other").lower().strip()
        # Guard: never create a genre with a blacklisted slug
        if slug in self._INTERNAL_GENRE_BLACKLIST:
            import logging
            logging.getLogger(__name__).warning(
                f"[GENRE_BLACKLIST] Refused to create genre for blacklisted slug='{slug}'"
            )
            return None
        name = name or slug.replace("-", " ").title()
        # Guard: if name is also blacklisted, derive a clean title from the slug
        if str(name).lower().strip() in self._INTERNAL_GENRE_BLACKLIST:
            name = slug.replace("-", " ").title()
        name_ar, name_en = FRONTEND_CATEGORY_LABELS.get(slug, (name, name))'''

assert OLD_2 in src, "Fix 2: target not found"
src = src.replace(OLD_2, NEW_2, 1)
print("Fix 2 applied: _get_or_create_genre guard")

# ── Fix 3: Guard _upsert_event_shell against using "internal" as genre name
OLD_3 = '''            if genre_slug:
                genre_id = await self._get_or_create_genre(db, genre_slug, ev.get("category") or ev.get("type") or genre_slug)
                self.metrics["categorized"] += 1
            else:
                self.metrics["uncategorized"] += 1
                logger.warning(f"[TAXONOMY_MISS] No genre resolved for slug: {slug}")'''

NEW_3 = '''            # Never create a genre from raw Webook API "type" field (e.g. "internal")
            ev_type = str(ev.get("type") or "").lower().strip()
            raw_name = (
                ev.get("category")
                or (ev_type if ev_type not in self._INTERNAL_GENRE_BLACKLIST else None)
                or genre_slug
            )
            if genre_slug and genre_slug not in self._INTERNAL_GENRE_BLACKLIST:
                genre_id = await self._get_or_create_genre(db, genre_slug, raw_name)
                self.metrics["categorized"] += 1
            else:
                self.metrics["uncategorized"] += 1
                logger.warning(f"[TAXONOMY_MISS] No genre resolved for slug: {slug}")'''

assert OLD_3 in src, "Fix 3: target not found"
src = src.replace(OLD_3, NEW_3, 1)
print("Fix 3 applied: _upsert_event_shell genre name guard")

with open(ENGINE_PATH, "w", encoding="utf-8") as f:
    f.write(src)

print("\nAll patches applied successfully to", ENGINE_PATH)
