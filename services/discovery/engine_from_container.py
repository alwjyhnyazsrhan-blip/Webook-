import asyncio
import random
import re
import httpx
from core.database.postgres import AsyncSessionLocal
from database.models.discovery import Genre, LiveEvent, SeatMapCache
from modules.webook.client import WebookApiClient
from sqlalchemy import select, update, delete, and_, or_, func, text
from datetime import datetime, timezone, timedelta
from core.logging.logger import logger
import xml.etree.ElementTree as ET
import json
import html
from services.discovery.taxonomy import TaxonomyEngine
from services.discovery.metrics import discovery_metrics
_MOJIBAKE_MARKERS = ("├â", "├é", "├ó", "├»", "∩┐╜")


def _repair_mojibake_text(text: str) -> str:
    if not isinstance(text, str) or not any(marker in text for marker in _MOJIBAKE_MARKERS):
        return text

    candidates = [text]
    for source_encoding in ("latin1", "cp1252"):
        try:
            candidates.append(text.encode(source_encoding).decode("utf-8"))
        except Exception:
            continue

    def score(value: str) -> tuple[int, int, int]:
        suspicious = sum(value.count(marker) for marker in _MOJIBAKE_MARKERS)
        arabic = sum(1 for char in value if "\u0600" <= char <= "\u06ff")
        replacement_chars = value.count("∩┐╜")
        return (suspicious + replacement_chars, -arabic, len(value))

    return min(candidates, key=score)


def _markdownish_to_html(text: str) -> str:
    if not isinstance(text, str):
        return text

    text = re.sub(
        r"\[([^\]]+)\]\((https?://[^)]+)\)",
        lambda match: f'<a href="{html.escape(match.group(2), quote=True)}">{match.group(1)}</a>',
        text,
    )
    text = re.sub(r"`([^`]+)`", lambda match: f"<code>{html.escape(match.group(1))}</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", lambda match: f"<b>{match.group(1)}</b>", text)
    text = re.sub(r"\*([^*\n]+)\*", lambda match: f"<i>{match.group(1)}</i>", text)
    return text


def _normalize_telegram_text(text: str) -> str:
    text = _repair_mojibake_text(str(text or ""))
    if any(token in text for token in ("**", "*", "`", "](")):
        text = _markdownish_to_html(text)
    return text


WEBOOK_ORGS = [
    "webook",
    "riyadh-season",
    "jeddah-season",
    "diriyah-season",
    "saudi-pro-league",
    "mdl-beast",
    "general-entertainment-authority",
    "roshn",
    "ithra",
    "saudi-esports-federation",
    "formula1-saudi-arabian-grand-prix",
    "wwe",
    "saudia",
    "neom",
    "red-sea-international-film-festival",
    "ministry-of-culture",
    "alula",
    "saudi-tourism-authority",
    "king-abdulaziz-foundation",
    "taif-season",
    "aseer-season",
    "hail-season",
    "al-ahli",
    "al-shabab",
    "al-fateh",
    "al-kholood",
    "al-okhdood",
    "al-ettifaq",
    "esports-world-cup",
    "balad-beast",
    "al-nassr",
    "al-hilal",
    "al-ittihad",
    "al-qadsiah",
    "al-raed",
    "al-khaleej",
    "al-orubah",
    "al-riyadh",
    "al-weihda",
]

FRONTEND_SOURCE_PREFIX = "cf_%"

FRONTEND_CATEGORY_LABELS = {
    "restaurant-and-cafe": ("\u0627\u0644\u0645\u0637\u0627\u0639\u0645", "Restaurants"),
    "restaurants": ("\u0627\u0644\u0645\u0637\u0627\u0639\u0645", "Restaurants"),
    "theater": ("\u0627\u0644\u0645\u0633\u0631\u062d", "Theater"),
    "sports": ("\u0627\u0644\u0631\u064a\u0627\u0636\u0629", "Sports"),
    "sports-event": ("\u0627\u0644\u0631\u064a\u0627\u0636\u0629", "Sports"),
    "football": ("\u0643\u0631\u0629 \u0627\u0644\u0642\u062f\u0645", "Football"),
    "music-events": ("\u0627\u0644\u062d\u0641\u0644\u0627\u062a", "Music Events"),
    "experience": ("\u0627\u0644\u062a\u062c\u0627\u0631\u0628", "Experience"),
    "activities-adventures": ("\u0627\u0644\u0623\u0646\u0634\u0637\u0629 \u0648\u0627\u0644\u0645\u063a\u0627\u0645\u0631\u0627\u062a", "Activities & Adventures"),
    "kids": ("\u0627\u0644\u0623\u0637\u0641\u0627\u0644", "Kids"),
    "esports": ("\u0627\u0644\u0631\u064a\u0627\u0636\u0627\u062a \u0627\u0644\u0625\u0644\u0643\u062a\u0631\u0648\u0646\u064a\u0629", "Esports"),
    "riyadh-season": ("\u0645\u0648\u0633\u0645 \u0627\u0644\u0631\u064a\u0627\u0636", "Riyadh Season"),
    "jeddah-season": ("\u0645\u0648\u0633\u0645 \u062c\u062f\u0629", "Jeddah Season"),
    "saudi-pro-league": ("\u062f\u0648\u0631\u064a \u0631\u0648\u0634\u0646", "Saudi Pro League"),
    "al-ahli": ("\u0627\u0644\u0623\u0647\u0644\u064a", "Al Ahli"),
    "al-hilal": ("\u0627\u0644\u0647\u0644\u0627\u0644", "Al Hilal"),
    "al-nassr": ("\u0627\u0644\u0646\u0635\u0631", "Al Nassr"),
    "al-ittihad": ("\u0627\u0644\u0627\u062a\u062d\u0627\u062f", "Al Ittihad"),
    "al-shabab": ("\u0627\u0644\u0634\u0628\u0627\u0628", "Al Shabab"),
    "al-ettifaq": ("\u0627\u0644\u0627\u062a\u0641\u0627\u0642", "Al Ettifaq"),
}

COLLECTION_CATEGORY_FALLBACKS = {
    "experienceCollection": ("experience", "Experience"),
    "restaurantCollection": ("restaurant-and-cafe", "Restaurants"),
    "zoneCollection": ("experience", "Experience"),
    "eventCollection": ("experience", "Experience"),
}


class DiscoveryEngine:
    _sync_lock = None

    @classmethod
    def _get_sync_lock(cls):
        if cls._sync_lock is None:
            cls._sync_lock = asyncio.Lock()
        return cls._sync_lock

    def __init__(self):
        self.api = WebookApiClient()
        self.metrics = {
            "total_discovered": 0,
            "persisted": 0,
            "hydrated": 0,
            "categorized": 0,
            "uncategorized": 0,
            "403_failed": 0,
            "duplicate_skipped": 0
        }

    def _reset_metrics(self):
        self.metrics = {k: 0 for k in self.metrics}

    async def get_all_events(self, limit: int = 1000, include_unavailable: bool = False) -> list:
        async with AsyncSessionLocal() as db:
            VISIBLE_STATUSES = ["READY", "DISCOVERED", "PARTIAL", "HYDRATING"]
            query = select(LiveEvent).where(LiveEvent.hydration_status.in_(VISIBLE_STATUSES))
            
            # Show upcoming events, but do not hide records with missing starts_at
            now = datetime.now(timezone.utc)
            query = query.where(or_(LiveEvent.starts_at == None, LiveEvent.starts_at > now))
            query = query.where(LiveEvent.status.notin_(["PAST", "GHOST"]))
            
            if not include_unavailable:
                query = query.where(LiveEvent.status.in_(["AVAILABLE", "UNKNOWN", None]))
            
            query = query.order_by(LiveEvent.starts_at.asc()).limit(limit)
            result = await db.execute(query)
            return result.scalars().all()

    async def get_live_categories(self) -> list:
        async with AsyncSessionLocal() as db:
            # First try: strictly active genres
            stmt = select(Genre).where(Genre.is_active == True).order_by(Genre.name_ar.asc())
            result = await db.execute(stmt)
            cats = result.scalars().all()
            
            logger.info(f"[CATEGORY_READ] active_only=True count={len(cats)}")
            
            # If no active genres, check if we need to bootstrap or fallback
            if not cats:
                # Emergency Fallback 1: Any genre that actually has visible events
                fallback_stmt = (
                    select(Genre)
                    .join(LiveEvent, LiveEvent.genre_id == Genre.id)
                    .where(LiveEvent.status != "GHOST")
                    .where(LiveEvent.hydration_status.in_(["READY", "DISCOVERED", "PARTIAL", "HYDRATING"]))
                    .distinct()
                    .order_by(Genre.name_ar.asc())
                )
                fallback = (await db.execute(fallback_stmt)).scalars().all()
                
                if fallback:
                    logger.info(f"[CATEGORY_FALLBACK] found {len(fallback)} genres with visible events (is_active flag was False)")
                    return fallback

                # Emergency Fallback 2: Bootstrap if table is empty
                all_genres_count = (await db.execute(select(func.count(Genre.id)))).scalar() or 0
                if all_genres_count == 0:
                    logger.warning("[CATEGORY_BOOTSTRAP] genres table empty, bootstrapping...")
                    await self._bootstrap_genres(db)
                    # Re-check after bootstrap (they will be is_active=False though, so we'll likely hit fallback next time)
                    result = await db.execute(stmt)
                    cats = result.scalars().all()

            return cats

    async def _check_all_genres(self) -> dict:
        async with AsyncSessionLocal() as db:
            all_g = (await db.execute(select(Genre))).scalars().all()
            active = [g.slug for g in all_g if g.is_active]
            all_slugs = [g.slug for g in all_g]
            return {"total": len(all_g), "active": active, "all_slugs": all_slugs}

    async def get_events_by_genre(self, genre_slug: str) -> list:
        async with AsyncSessionLocal() as db:
            genre_stmt = select(Genre).where(Genre.slug == genre_slug)
            genre = (await db.execute(genre_stmt)).scalar_one_or_none()
            if not genre:
                return []
            VISIBLE_STATUSES = ["READY", "DISCOVERED", "PARTIAL", "HYDRATING"]
            now = datetime.now(timezone.utc)
            stmt = select(LiveEvent).where(
                and_(
                    LiveEvent.genre_id == genre.id,
                    LiveEvent.hydration_status.in_(VISIBLE_STATUSES),
                    LiveEvent.status.notin_(["PAST", "GHOST"]),
                    or_(LiveEvent.starts_at == None, LiveEvent.starts_at > now)
                )
            ).order_by(LiveEvent.starts_at.asc())
            result = await db.execute(stmt)
            return result.scalars().all()

    async def _bootstrap_genres(self, db):
        activated = []
        all_taxonomy_slugs = TaxonomyEngine.get_all_genre_slugs()
        
        # Combine static WEBOOK_ORGS with dynamic taxonomy slugs
        bootstrap_slugs = set(WEBOOK_ORGS) | all_taxonomy_slugs
        
        for slug in bootstrap_slugs:
            stmt = select(Genre).where(Genre.slug == slug)
            existing = (await db.execute(stmt)).scalar_one_or_none()
            if not existing:
                name = slug.replace("-", " ").title()
                new_genre = Genre(
                    name_ar=name,
                    name_en=name,
                    slug=slug,
                    is_active=False
                )
                db.add(new_genre)
            # We don't reset is_active here; activation happens in _activate_genres_with_events
            activated.append(slug)
            
        await db.commit()
        logger.info(f"[GENRE_BOOTSTRAP] count={len(activated)} total_potential_genres={len(bootstrap_slugs)}")

    async def sync_all(self):
        lock = self._get_sync_lock()
        if lock.locked():
            logger.warning("[SYNC_SKIPPED] Discovery sync already running")
            return 0
        async with lock:
            return await self._sync_all_locked()

    async def _sync_all_locked(self):
        logger.info("DiscoveryEngine: STAGE 1 (Aggressive Discovery) started")
        self._reset_metrics()

        async with AsyncSessionLocal() as db:
            await self._bootstrap_genres(db)

            # 1. DYNAMIC ORGANIZATION DISCOVERY
            all_orgs = self.api.KNOWN_ORGS
            try:
                logger.info("[DISCOVERY] Fetching dynamic organization list...")
                org_data = await self.api.get_organizations()
                discovered_orgs = []
                if isinstance(org_data, dict):
                    raw_list = org_data.get("data", {}).get("data", []) if isinstance(org_data.get("data"), dict) else org_data.get("data", [])
                    if isinstance(raw_list, list):
                        discovered_orgs = [o.get("slug") for o in raw_list if o.get("slug")]
                
                # Merge with fallback list to ensure we don't miss anything
                all_orgs = list(set(discovered_orgs + self.api.KNOWN_ORGS))
                logger.info(f"[DISCOVERY] Found {len(discovered_orgs)} dynamic orgs. Total to sync: {len(all_orgs)}")
            except Exception as e:
                logger.error(f"DiscoveryEngine: Dynamic Org Discovery failed: {e}")

            logger.info("[SYNC_BLOCK_A] About to execute global discovery")
            try:
                logger.info("[SYNC_STARTED] Global Discovery (Exhaustive)")
                res = await self.api.get_all_upcoming_events(per_page=50, exhaustive=True, orgs=all_orgs)
                events = res.get("events", [])
                total_api = res.get("total", 0)
                logger.info(f"[API_RESPONSE] Received {len(events)} events | Total Reported={total_api}")

                for ev in events:
                    slug = ev.get("slug", "")
                    org_slug = ev.get("organization_slug") or ev.get("organization", {}).get("slug")
                    genre_id_fk = await TaxonomyEngine.resolve_genre_id(db, slug, title=ev.get("title"), category=ev.get("category"), org_slug=org_slug)
                    await self._upsert_event_shell(db, ev, genre_id=genre_id_fk)
                    self.metrics["total_discovered"] += 1
                await db.commit()
            except Exception as e:
                logger.error(f"DiscoveryEngine: Global Discovery failed: {e}")

            # 2. INDIVIDUAL ORGANIZATION DISCOVERY (Redundant but safe fallback)
            for org in all_orgs:
                    try:
                        logger.info(f"[SYNC_STARTED] Organization: {org}")
                        org_count = await self._sync_organization_shell(db, org)
                        logger.info(f"[SYNC_FINISHED] Organization: {org} | Synced={org_count}")
                        self.metrics["total_discovered"] += org_count
                    except Exception as e:
                        logger.error(f"DiscoveryEngine: Org Discovery failed for {org}: {e}")
            # 2. DYNAMIC GENRE DISCOVERY
            try:
                logger.info("[DISCOVERY] Fetching dynamic genre list...")
                genres = await self.api.get_genres()
                if genres:
                    for g in genres:
                        slug = g.get("slug")
                        if not slug: continue
                        try:
                            logger.info(f"[SYNC_STARTED] Genre: {slug}")
                            res = await self.api.get_events_by_genre(slug)
                            evs = res.get("data", {}).get("data", []) if isinstance(res.get("data"), dict) else res.get("data", [])
                            if isinstance(evs, list):
                                for ev in evs:
                                    await self._upsert_event_shell(db, ev)
                                    self.metrics["total_discovered"] += 1
                            logger.info(f"[SYNC_FINISHED] Genre: {slug} | Found={len(evs) if isinstance(evs, list) else 0}")
                        except Exception as e:
                            logger.error(f"DiscoveryEngine: Genre Discovery failed for {slug}: {e}")
            except Exception as e:
                logger.error(f"DiscoveryEngine: Dynamic Genre Discovery failed: {e}")

            for term in ["riyadh", "jeddah", "season", "concert", "match", "cup", "league"]:
                try:
                    events = await self.api.search_events(term)
                    if events:
                        for ev in events:
                            await self._upsert_event_shell(db, ev)
                            self.metrics["total_discovered"] += 1
                        await db.commit()
                except Exception:
                    pass

            try:
                logger.info("[SYNC_STARTED] Sitemap Exhaustive Scan")
                sitemap_count = await self._sync_from_sitemap(db)
                logger.info(f"[SYNC_FINISHED] Sitemap Scan | New={sitemap_count}")
                self.metrics["total_discovered"] += sitemap_count
            except Exception as e:
                logger.error(f"DiscoveryEngine: Sitemap Discovery failed: {e}")

            try:
                logger.info("[BACKFILL_START] Running genre derivation backfill")
                backfill_count = await self._backfill_genre_derivation(db)
                logger.info(f"[SYNC_FINISHED] Genre Backfill | Updated={backfill_count}")
            except Exception as e:
                logger.error(f"DiscoveryEngine: Genre Backfill failed: {e}")

            await self._activate_genres_with_events(db)
            await self._purge_stale_events(db)

        await self.hydrate_all(concurrency=5)

        discovery_metrics.update(self.metrics)
        logger.info(f"DiscoveryEngine: Stage 1 Complete. Final Metrics: {self.metrics}")
        return self.metrics["total_discovered"]

    async def _purge_stale_events(self, db):
        """
        Conservative cleanup that avoids removing valid upcoming events.
        """
        now = datetime.now(timezone.utc)
        yesterday = now - timedelta(days=1)
        
        # 1. Delete only explicit stale statuses older than 24h
        stmt = delete(LiveEvent).where(
            and_(
                LiveEvent.status.in_(["SOLD_OUT", "PAST"]),
                LiveEvent.starts_at != None,
                LiveEvent.starts_at < yesterday,
            )
        )
        res = await db.execute(stmt)
        logger.info(f"[PURGE] Deleted {res.rowcount} stale/past events")
        
        # 2. Ghost events that are stale for 48h and still unverified
        stale_threshold = now - timedelta(hours=48)
        ghost_stmt = update(LiveEvent).where(
            and_(
                LiveEvent.status == "AVAILABLE",
                LiveEvent.last_verified_at != None,
                LiveEvent.last_verified_at < stale_threshold
            )
        ).values(status="GHOST")
        res = await db.execute(ghost_stmt)
        logger.info(f"[PURGE] Ghosted {res.rowcount} unverified events")
        
        await db.commit()

    async def _sync_organization_shell(self, db, org_slug: str) -> int:
        logger.info(f"[API_FETCH] Org={org_slug} (Exhaustive)")
        result = await self.api.get_events_by_organization(org_slug, per_page=50, exhaustive=True)
        events = result.get("events", [])
        total_org = result.get("total", 0)
        logger.info(f"[API_RESPONSE] Org={org_slug} | Received {len(events)} events | Total Reported={total_org}")

        synced_count = 0
        for ev in events:
            if isinstance(ev, dict) and not ev.get("organization_slug"):
                ev["organization_slug"] = org_slug
            await self._upsert_event_shell(db, ev)
            synced_count += 1
        
        await db.commit()

        return synced_count


    async def _backfill_genre_derivation(self, db) -> int:
        uncategorized = (await db.execute(
            select(LiveEvent).where(LiveEvent.genre_id == None)
        )).scalars().all()
        updated = 0
        for ev in uncategorized:
            metadata = ev.metadata_json or {}
            org_slug = metadata.get("organization_slug") or metadata.get("organization", {}).get("slug")
            category = metadata.get("category")
            genre_slug = TaxonomyEngine.resolve_genre_slug(
                ev.slug,
                title=ev.title_ar or ev.title_en,
                category=category,
                org_slug=org_slug,
            )
            genre_id = await self._get_or_create_genre(db, genre_slug, category or genre_slug) if genre_slug else None
            if genre_id:
                ev.genre_id = genre_id
                updated += 1
                logger.info(f"[GENRE_BACKFILL] slug={ev.slug} genre_id={genre_id}")
        if updated > 0:
            await db.commit()
            logger.info(f"[GENRE_BACKFILL] Committed {updated} genre updates")
        return updated

    async def _activate_genres_with_events(self, db):
        stmt = select(Genre)
        genres = (await db.execute(stmt)).scalars().all()
        
        for genre in genres:
            # Skip already active genres if we want to be efficient, 
            # but re-checking ensures they are actually still relevant.
            
            cnt_stmt = select(func.count(LiveEvent.id)).where(
                and_(
                    LiveEvent.genre_id == genre.id,
                    LiveEvent.hydration_status.in_(["READY", "HYDRATING", "DISCOVERED"])
                )
            )
            event_count = (await db.execute(cnt_stmt)).scalar() or 0
            
            if event_count > 0:
                if not genre.is_active:
                    genre.is_active = True
                    logger.info(f"[GENRE_ACTIVATED] slug={genre.slug} id={genre.id} events={event_count}")
            else:
                if genre.is_active:
                    genre.is_active = False
                    logger.info(f"[GENRE_DEACTIVATED] slug={genre.slug} id={genre.id} (No events)")
        
        await db.commit()

    async def hydrate_all(self, batch_size: int = 50, concurrency: int = 5):
        logger.info(f"DiscoveryEngine: STAGE 2 (Hydration) started | Concurrency={concurrency}")

        stats = {"total": 0, "success": 0, "failed": 0, "charts": 0, "images": 0, "retries": 0}

        async with AsyncSessionLocal() as db:
            stmt = select(LiveEvent).where(
                and_(
                    LiveEvent.hydration_status.in_(["DISCOVERED", "FAILED", "PARTIAL"]),
                    LiveEvent.hydration_attempts < 5
                )
            ).limit(batch_size)

            res = await db.execute(stmt)
            tasks = res.scalars().all()

            if not tasks:
                logger.info("DiscoveryEngine: No events requiring hydration.")
                return stats

            stats["total"] = len(tasks)
            from database.repositories.account import AccountRepository
            monitor_acc = await AccountRepository(db).get_sniper_account()

            client = self.api
            if monitor_acc:
                client = WebookApiClient(bearer_token=monitor_acc.bearer_token)

            sem = asyncio.Semaphore(concurrency)

            async def _worker(event_id: int):
                async with sem:
                    # Pacing & Jitter (Priority 3)
                    await asyncio.sleep(random.uniform(1.0, 3.0))
                    async with AsyncSessionLocal() as task_db:
                        try:
                            stmt = select(LiveEvent).where(LiveEvent.id == event_id)
                            event = (await task_db.execute(stmt)).scalar_one_or_none()
                            if not event:
                                return

                            event.hydration_attempts += 1
                            success = await self._hydrate_event(task_db, event, client)
                            if success:
                                stats["success"] += 1
                                await task_db.commit()
                            else:
                                stats["failed"] += 1
                                await task_db.commit()
                        except Exception as e:
                            logger.error(f"Hydration Crash for event_id {event_id}: {e}")
                            stats["failed"] += 1

            await asyncio.gather(*[_worker(e.id) for e in tasks])

            stats["charts"] = (await db.execute(select(func.count(LiveEvent.id)).where(LiveEvent.chart_token != None))).scalar()
            stats["images"] = (await db.execute(select(func.count(LiveEvent.id)).where(LiveEvent.image_url != None))).scalar()

        logger.info(f"DiscoveryEngine: Hydration Cycle Complete | {stats}")
        return stats

    async def sync_event_detail(self, slug: str, bearer_token: str = None) -> dict:
        """
        Public-facing event hydration.
        Returns the raw event detail from the Webook API.
        """
        try:
            if bearer_token:
                client = WebookApiClient(bearer_token=bearer_token)
            else:
                client = self.api
                
            logger.info(f"[SYNC_DETAIL] Fetching detail for slug={slug}")
            detail = await client.get_event_detail(slug)
            return detail.get("data", detail) if isinstance(detail, dict) else {}
        except Exception as e:
            logger.error(f"[SYNC_DETAIL_FAIL] slug={slug} error={e}")
            return {}

    async def _hydrate_event(self, db, event: LiveEvent, client: WebookApiClient) -> bool:
        correlation_id = f"HYD-{event.slug}"
        logger.info(f"[{correlation_id}] Hydration Start (Attempt {event.hydration_attempts})")

        event.hydration_status = "HYDRATING"
        await db.flush()

        try:
            detail = await asyncio.wait_for(client.get_event_detail(event.slug), timeout=15.0)
            if not detail:
                event.hydration_status = "FAILED"
                event.last_hydration_error = "EMPTY_API_RESPONSE"
                return False

            data = detail.get("data", detail) if isinstance(detail, dict) else {}

            if not data or not isinstance(data, dict):
                prefixes = ["experience-detail", "restaurant-detail", "package-detail", "zone-detail"]
                found_fallback = False
                for p in prefixes:
                    logger.info(f"[{correlation_id}] Trying fallback prefix: {p}")
                    detail = await client._request("GET", f"{client.BASE_URL}/{p}/{event.slug}", params={"lang": "ar", "visible_in": "webook"})
                    if detail.status_code == 200:
                        data = detail.json().get("data", detail.json())
                        found_fallback = True
                        break

                if not found_fallback:
                    event.hydration_status = "FAILED"
                    event.last_hydration_error = "INVALID_PAYLOAD_STRUCTURE"
                    return False

            event.title_ar = data.get("title") or event.title_ar

            venue = data.get("venue", {})
            if isinstance(venue, dict):
                event.venue_name = venue.get("name") or event.venue_name
                event.venue_address = venue.get("address") or event.venue_address
                event.venue_lat = str(venue.get("lat", "")) or event.venue_lat
                event.venue_lng = str(venue.get("lng", "")) or event.venue_lng

            images = data.get("images", [])
            img_url = None
            if isinstance(images, list) and len(images) > 0:
                img_url = images[0].get("url")

            if not img_url:
                img_url = data.get("promo_poster") or data.get("mobile_poster") or data.get("poster")

            if img_url:
                event.image_url = img_url

            event.min_price = data.get("min_price") or event.min_price

            event.seats_provider = data.get("seats_provider") or data.get("seatsProvider")
            seats_io = data.get("seats_io") or data.get("seatsIo") or data.get("seats") or {}
            if not isinstance(seats_io, dict):
                seats_io = {}
            event.chart_key = (
                seats_io.get("chart_key") or seats_io.get("chartKey")
                or seats_io.get("chart_token") or seats_io.get("chartToken")
                or data.get("chart_key") or data.get("chartKey")
            )
            event.event_key = (
                seats_io.get("event_key") or seats_io.get("eventKey")
                or seats_io.get("event_id") or seats_io.get("eventId")
                or data.get("event_key") or data.get("eventKey")
            )
            event.workspace_key = (
                seats_io.get("workspace_key") or seats_io.get("workspaceKey")
                or seats_io.get("workspace") or seats_io.get("workspaceId")
                or data.get("workspace_key") or data.get("workspaceKey")
            )
            
            # Extract Seat Map and Eagle Eye images
            event.seat_map_image = data.get("seat_map_image") or data.get("seat_map") or data.get("stadium_map_url")
            event.eagle_eye_image = data.get("eagle_eye_image") or data.get("eagle_eye")
            
            # If still missing, check contentful/metadata
            if not event.eagle_eye_image:
                contentful = data.get("contentful", {})
                if isinstance(contentful, dict):
                    event.eagle_eye_image = contentful.get("eagle_eye_image") or contentful.get("eagleEye")

            event.interactive_map_url = f"https://webook.com/ar/events/{event.slug}"
            event.last_verified_at = datetime.now(timezone.utc)
            
            # Accurate Event Scheduling
            start_ts = data.get("start_date_time") or data.get("startDate")
            if start_ts:
                try:
                    if isinstance(start_ts, (int, float)):
                        event.starts_at = datetime.fromtimestamp(int(start_ts), tz=timezone.utc)
                    elif isinstance(start_ts, str):
                        event.starts_at = datetime.fromisoformat(start_ts.replace("Z", "+00:00"))
                except Exception:
                    pass
            
            # Accurate Status Handling
            now = datetime.now(timezone.utc)
            is_soldout = data.get("is_soldout") or data.get("is_sold_out") or data.get("sold_out")
            api_status = str(data.get("status") or "").lower()
            tickets = data.get("event_tickets") or data.get("ticket_packages") or []
            
            if is_soldout or api_status == "past" or (event.starts_at and event.starts_at < now):
                event.status = "SOLD_OUT"
            elif not tickets and api_status != "upcoming" and not data.get("is_seated"):
                event.status = "SOLD_OUT"
            else:
                # Deep Availability Check: Ensure at least one ticket is actually bookable
                has_live_inventory = False
                if isinstance(tickets, list):
                    for t in tickets:
                        t_sold = t.get("is_soldout") or t.get("is_sold_out") or t.get("sold_out")
                        t_rem = t.get("remaining") or t.get("available")
                        if t_sold is False or (t_rem is not None and int(t_rem) > 0):
                            has_live_inventory = True
                            break
                        if t_sold is None and t_rem is None and str(t.get("status", "")).lower() in ("active", "available"):
                            has_live_inventory = True
                            break

                if (not tickets or not has_live_inventory) and api_status != "upcoming" and not data.get("is_seated"):
                    event.status = "SOLD_OUT"
                else:
                    event.status = "AVAILABLE"

            event.metadata_json = data
            event.hydration_status = "READY"
            event.hydrated_at = datetime.now(timezone.utc)
            event.last_hydration_error = None

            logger.info(f"[{correlation_id}] Hydration SUCCESS | State: {event.hydration_status} | Status: {event.status}")
            return True

        except asyncio.TimeoutError:
            event.last_hydration_error = "TIMEOUT"
            event.hydration_status = "FAILED"
            return False
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 403:
                self.metrics["403_failed"] += 1
            event.last_hydration_error = f"HTTP_{e.response.status_code}"
            event.hydration_status = "FAILED"
            return False
        except Exception as e:
            event.last_hydration_error = str(e)
            event.hydration_status = "FAILED"
            return False

    async def _sync_from_sitemap(self, db) -> int:
        seen_slugs = set()

        result = await db.execute(select(LiveEvent.slug))
        for row in result:
            seen_slugs.add(row[0])

        http_client = httpx.AsyncClient(timeout=10.0, headers={
            "User-Agent": "Mozilla/5.0 (compatible; webook-bot/1.0)",
            "token": "e9aac1f2f0b6c07d6be070ed14829de684264278359148d6a582ca65a50934d2",
            "Origin": "https://webook.com",
            "Referer": "https://webook.com/",
            "Accept": "application/json, text/plain, */*",
        })

        # Correct Webook Sitemap Pattern
        sitemaps = [
            "https://webook.com/sitemap-events.xml",
            "https://webook.com/sitemap-tournaments.xml",
            "https://webook.com/sitemap-organizations.xml",
        ]

        for sitemap_url in sitemaps:
            try:
                resp = await http_client.get(sitemap_url)
                if resp.status_code != 200:
                    logger.info(f"[SITEMAP_FETCH_FAIL] url={sitemap_url} status={resp.status_code}")
                    continue
                locs = re.findall(r"<loc>([^<]+)</loc>", resp.text)
                if not locs:
                    continue
                logger.info(f"[SITEMAP_LOADED] url={sitemap_url} urls_count={len(locs)}")

                for loc in locs:
                    slug = self._extract_slug_from_url(loc)
                    if not slug or slug in seen_slugs:
                        self.metrics["duplicate_skipped"] += 1
                        continue
                    seen_slugs.add(slug)

                    ev = {"slug": slug, "webook_id": f"cf_{slug}"}
                    category = ""

                    try:
                        # Use the new authenticated endpoint for sitemap hydration
                        detail = await self.api.get_event_detail(slug)
                        if isinstance(detail, dict):
                            inner = detail.get("data", detail)
                            if not isinstance(inner, dict):
                                inner = {}
                            ev = {
                                "slug": slug,
                                "webook_id": inner.get("_id") or inner.get("id") or f"cf_{slug}",
                                "title": inner.get("title") or slug,
                                "type": inner.get("type") or "internal",
                                "category": inner.get("category") or "",
                                "is_seated": inner.get("is_seated") or False,
                                "is_experience": inner.get("is_experience") or False,
                                "is_show": inner.get("is_show") or False,
                            }
                            category = inner.get("category") or ""
                            self.metrics["hydrated"] += 1
                        else:
                            ev["title"] = slug.replace("-", " ").title()
                    except Exception as e:
                        logger.warning(f"[SITEMAP_DETAIL_FAIL] slug={slug} error={e}")
                        ev["title"] = slug.replace("-", " ").title()

                    title = ev.get("title") or slug.replace("-", " ").title()
                    category = ev.get("category", "")
                    org_slug = ev.get("organization_slug") or ev.get("organization", {}).get("slug")
                    
                    genre_id_fk = await TaxonomyEngine.resolve_genre_id(db, slug, title, category, org_slug)
                    
                    if genre_id_fk:
                        self.metrics["categorized"] += 1
                    else:
                        self.metrics["uncategorized"] += 1

                    logger.info(f"[SITEMAP_PROCESS] slug={slug} genre_id={genre_id_fk}")
                    await self._upsert_event_shell(db, ev, genre_id=genre_id_fk)
                    self.metrics["total_discovered"] += 1

                await db.commit()
                await asyncio.sleep(0.5)
            except Exception as e:
                logger.error(f"[SITEMAP_ERROR] url={sitemap_url} error={e}")

        await http_client.aclose()

        logger.info(f"[SITEMAP_SYNC] Metrics: {self.metrics}")
        return self.metrics["total_discovered"]


    def _extract_slug_from_url(self, url: str) -> str:
        match = re.search(r"/events/([^/]+)", url)
        if match:
            return match.group(1).split("/")[0].split("?")[0]
        return ""

    async def _upsert_event_shell(self, db, ev: dict, genre_id: int = None):
        webook_id = str(ev.get("_id") or ev.get("id") or "")
        slug = ev.get("slug", "")
        ev_keys = list(ev.keys()) if ev else []

        if not slug:
            logger.warning(f"Skipping event: missing slug. Keys: {ev_keys}")
            return

        if not webook_id:
            webook_id = f"cf_{slug}"

        if genre_id is None:
            org_slug = ev.get("organization_slug") or ev.get("organization", {}).get("slug")
            genre_slug = TaxonomyEngine.resolve_genre_slug(
                slug,
                title=ev.get("title"),
                category=ev.get("category"),
                org_slug=org_slug,
            )
            if genre_slug:
                genre_id = await self._get_or_create_genre(db, genre_slug, ev.get("category") or ev.get("type") or genre_slug)
                self.metrics["categorized"] += 1
            else:
                self.metrics["uncategorized"] += 1
                logger.warning(f"[TAXONOMY_MISS] No genre resolved for slug: {slug}")
        else:
            self.metrics["categorized"] += 1

        stmt = select(LiveEvent).where(LiveEvent.slug == slug)
        existing = (await db.execute(stmt)).scalar_one_or_none()
        if not existing:
            stmt = select(LiveEvent).where(LiveEvent.webook_id == webook_id)
            existing = (await db.execute(stmt)).scalar_one_or_none()

        if not existing:
            existing = LiveEvent(
                webook_id=webook_id,
                slug=slug,
                title_ar=ev.get("title") or ev.get("name") or slug,
                title_en=ev.get("title") or ev.get("name") or slug,
                genre_id=genre_id,
                hydration_status="DISCOVERED"
            )
            db.add(existing)
            self.metrics["persisted"] += 1
            logger.info(f"[SITEMAP_UPSERT] NEW slug={slug} webook_id={webook_id} genre_id={genre_id}")
        else:
            self.metrics["duplicate_skipped"] += 1
            logger.info(f"[SITEMAP_EXISTS] slug={slug} existing_webook_id={existing.webook_id}")
            if webook_id.startswith("cf_") and existing.webook_id != webook_id:
                logger.info(f"[EVENT_DISCOVERED] Promoting slug={slug} to frontend source webook_id={webook_id}")
                existing.webook_id = webook_id
            else:
                existing.webook_id = existing.webook_id or webook_id
            existing.title_ar = ev.get("title") or ev.get("name") or existing.title_ar
            existing.title_en = ev.get("title") or ev.get("name") or existing.title_en
            existing.genre_id = genre_id if genre_id else existing.genre_id

        start_ts = ev.get("start_date_time") or ev.get("open_date_time") or ev.get("starts_at")
        if start_ts:
            try:
                if isinstance(start_ts, (int, float)):
                    existing.starts_at = datetime.fromtimestamp(start_ts, tz=timezone.utc)
                elif isinstance(start_ts, str):
                    from dateutil.parser import parse as parse_date
                    existing.starts_at = parse_date(start_ts)
                    if existing.starts_at.tzinfo is None:
                        existing.starts_at = existing.starts_at.replace(tzinfo=timezone.utc)
            except Exception as e:
                logger.warning(f"[DATE_PARSE_FAIL] slug={slug} val={start_ts} err={e}")

        # STRICT: If event is in the past, mark as PAST
        now = datetime.now(timezone.utc)
        if existing.starts_at and existing.starts_at < now:
            existing.status = "PAST"
            existing.hydration_status = "PAST"
        else:
            existing.status = ev.get("status", "AVAILABLE").upper()
            if existing.status in ("PAST", "ENDED", "FINISHED"):
                existing.status = "PAST"

        venue = ev.get("venue") or {}
        if isinstance(venue, dict):
            existing.venue_name = venue.get("name") or venue.get("city")
        elif isinstance(venue, str):
            existing.venue_name = venue

        existing.min_price = ev.get("min_price")
        existing.max_price = ev.get("max_price")

        existing.metadata_json = ev

        chart = self._find_chart_token_recursive(ev)
        if chart:
            existing.chart_key = existing.chart_key or chart
            existing.stadium_map_url = chart

        image_url = ev.get("image_url")
        if image_url:
            existing.image_url = image_url

    async def _get_or_create_genre(self, db, slug: str, name: str) -> int:
        slug = slug or "other"
        name = name or slug.replace("-", " ").title()
        name_ar, name_en = FRONTEND_CATEGORY_LABELS.get(slug, (name, name))
        stmt = select(Genre).where(Genre.slug == slug)
        genre = (await db.execute(stmt)).scalar_one_or_none()
        if not genre:
            genre = Genre(name_ar=name_ar, name_en=name_en, slug=slug, is_active=True)
            db.add(genre)
            await db.flush()
        else:
            genre.name_ar = name_ar or genre.name_ar
            genre.name_en = name_en or genre.name_en
            genre.is_active = True
        return genre.id

    def _find_chart_token_recursive(self, obj, _path="root") -> str:
        if isinstance(obj, dict):
            for key in ["chart_key", "chartKey", "chart_token", "chartToken"]:
                if key in obj and obj[key]:
                    return str(obj[key])
            for key, value in obj.items():
                result = self._find_chart_token_recursive(value, f"{_path}.{key}")
                if result:
                    return result
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                result = self._find_chart_token_recursive(item, f"{_path}[{i}]")
                if result:
                    return result
        return None

    async def get_event_tickets_live(self, slug: str) -> dict:
        try:
            result = await self.api.get_event_tickets(slug, lang="ar")
            if result and result.get("event_tickets"):
                return result
        except Exception as e:
            logger.warning(f"[TICKETS_LIVE_PRIMARY] slug={slug} error={e}")

        # FIX: Fallback to availability endpoint if primary fails
        try:
            logger.info(f"[TICKETS_LIVE_FALLBACK] slug={slug}")
            fallback = await self.api.get_event_availability(slug, lang="ar")
            if fallback:
                return fallback
        except Exception as fallback_err:
            logger.error(f"[TICKETS_LIVE_FALLBACK_FAILED] slug={slug} error={fallback_err}")

        return {}

    async def send_daily_summary(self):
        try:
            from core.config.settings import settings
            from core.database.postgres import AsyncSessionLocal
            from database.models.discovery import LiveEvent
            from sqlalchemy import select, func

            if not settings.admin_ids:
                logger.warning("No admin_ids configured")
                return

            async with AsyncSessionLocal() as db:
                total_events = await db.scalar(select(func.count(LiveEvent.id)))
                ready_events = await db.scalar(select(func.count(LiveEvent.id)).where(LiveEvent.hydration_status == "READY"))
                ghost_events = await db.scalar(select(func.count(LiveEvent.id)).where(LiveEvent.status == "GHOST"))

            msg = (
                f"\U0001f4ca *\u062a\u0642\u0631\u064a\u0631 \u064a\u0648\u0645\u064a - Webook Bot*\n\n"
                f"\U0001f50d \u0625\u062c\u0645\u0627\u0644\u064a \u0627\u0644\u0641\u0639\u0627\u0644\u064a\u0627\u062a: {total_events or 0}\n"
                f"\u2705 \u062c\u0627\u0647\u0632\u0629 \u0644\u0644\u062d\u062c\u0632: {ready_events or 0}\n"
                f"\U0001f47b \u062c\u062f\u064a\u062f\u0629 (\u0627\u0644\u0645\u0631\u0627\u0642\u0628\u0629): {ghost_events or 0}\n\n"
                f"\U0001f916 \u062d\u0627\u0644\u0629 \u0627\u0644\u0646\u0638\u0627\u0645: \u0627\u0644\u062a\u0634\u063a\u064a\u0644 \u0627\u0644\u0639\u0627\u062f\u064a"
            )

            from apps.bot.main import bot
            for admin_id in settings.admin_ids:
                try:
                    await bot.send_message(admin_id, _normalize_telegram_text(msg), parse_mode="HTML")
                except Exception as send_err:
                    logger.warning(f"Daily summary failed for admin {admin_id}: {send_err}")

            logger.info(f"Daily summary sent to admins")
        except Exception as e:
            logger.error("Daily summary failed: " + str(e))
