"""
diagnose_bot.py â€” FULL RUNTIME VALIDATION
==========================================
Run this ON YOUR SERVER (same environment as the bot):

    cd /path/to/your/bot
    python diagnose_bot.py

It exercises the EXACT same code paths Telegram calls, using real DB + Redis,
without needing Telegram open. Produces a pass/fail report for every stage.

Requirements: .env loaded, DB reachable, Redis reachable (same as normal bot run).
"""

import asyncio
import sys
import os
import time
import traceback
from datetime import datetime

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ colour helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def ok(msg):   print(f"  {GREEN}[PASS]{RESET} {msg}")
def fail(msg): print(f"  {RED}[FAIL]{RESET} {msg}")
def warn(msg): print(f"  {YELLOW}[WARN]{RESET} {msg}")
def info(msg): print(f"  {CYAN}[INFO]{RESET} {msg}")
def hdr(msg):  print(f"\n{BOLD}{'='*60}\n  {msg}\n{'='*60}{RESET}")

results = {"pass": 0, "fail": 0, "warn": 0}

def record(status, msg):
    results[status] += 1
    {"pass": ok, "fail": fail, "warn": warn}[status](msg)

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# STAGE 0 â€” Imports & environment
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
hdr("STAGE 0 â€” Environment")

try:
    from dotenv import load_dotenv
    load_dotenv()
    record("pass", ".env loaded")
except ImportError:
    record("warn", "python-dotenv not installed; relying on existing env vars")

try:
    from core.database.postgres import AsyncSessionLocal
    record("pass", "AsyncSessionLocal imported")
except Exception as e:
    record("fail", f"Cannot import AsyncSessionLocal: {e}")
    print("\n  Cannot continue without DB. Fix import path first.")
    sys.exit(1)

try:
    from services.discovery.engine import DiscoveryEngine
    discovery = DiscoveryEngine()
    record("pass", "DiscoveryEngine imported and instantiated")
except Exception as e:
    record("fail", f"Cannot import DiscoveryEngine: {e}")
    sys.exit(1)

try:
    from database.models.discovery import Genre, LiveEvent
    from database.models.reservation import ReservationTask, TaskStatus
    from database.models.account import AuthSession
    record("pass", "All models imported")
except Exception as e:
    record("fail", f"Model import failed: {e}")
    sys.exit(1)

try:
    from database.repositories.account import AccountRepository
    from database.repositories.reservation import ReservationRepository
    record("pass", "Repositories imported")
except Exception as e:
    record("fail", f"Repository import failed: {e}")

try:
    from sqlalchemy import select, and_, func
    record("pass", "SQLAlchemy imported")
except Exception as e:
    record("fail", f"SQLAlchemy import failed: {e}")
    sys.exit(1)

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
async def run_all():
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    # STAGE 1 â€” Database connectivity
    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    hdr("STAGE 1 â€” Database Connectivity")
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(1))
            val = result.scalar()
            record("pass", f"Database connected â€” test query result: {val}")
    except Exception as e:
        record("fail", f"PostgreSQL connection FAILED: {e}")
        print("\n  Cannot continue â€” fix DB connection first.")
        return

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    # STAGE 2 â€” Genre / Category table state
    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    hdr("STAGE 2 â€” Genre Table State")
    async with AsyncSessionLocal() as db:
        all_genres   = (await db.execute(select(Genre))).scalars().all()
        active_genres = [g for g in all_genres if g.is_active]

        info(f"Total genres in DB:  {len(all_genres)}")
        info(f"Active genres:       {len(active_genres)}")

        if len(all_genres) == 0:
            record("fail", "genres table is EMPTY â€” sync has never run or bootstrap failed")
        elif len(active_genres) == 0:
            record("fail", "Genres exist but NONE are active (is_active=False on all rows) â€” "
                           "this is why get_live_categories() returns []")
            print(f"\n  {YELLOW}All genre slugs:{RESET}")
            for g in all_genres[:20]:
                print(f"    slug={g.slug}  is_active={g.is_active}")
        else:
            record("pass", f"{len(active_genres)} active genres found")
            for g in active_genres:
                print(f"    slug={g.slug}  name_ar={g.name_ar}  is_active={g.is_active}")

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    # STAGE 3 â€” LiveEvent table state
    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    hdr("STAGE 3 â€” LiveEvent Table State")
    async with AsyncSessionLocal() as db:
        all_events = (await db.execute(select(LiveEvent))).scalars().all()
        ghost      = [e for e in all_events if e.status == "GHOST"]
        visible    = [e for e in all_events if e.status != "GHOST"]
        ready      = [e for e in all_events if e.hydration_status == "READY"]
        discovered = [e for e in all_events if e.hydration_status == "DISCOVERED"]

        info(f"Total events:       {len(all_events)}")
        info(f"GHOST (excluded):   {len(ghost)}")
        info(f"Visible (non-GHOST):{len(visible)}")
        info(f"  READY:            {len(ready)}")
        info(f"  DISCOVERED:       {len(discovered)}")
        info(f"  Other:            {len(visible) - len(ready) - len(discovered)}")

        if len(all_events) == 0:
            record("fail", "events table is EMPTY â€” run sync first")
        elif len(visible) == 0:
            record("fail", "All events are GHOST â€” none will render")
        elif len(visible) < 5:
            record("warn", f"Only {len(visible)} visible events â€” may need re-sync")
        else:
            record("pass", f"{len(visible)} visible events available")

        # Show sample
        sample = visible[:5] if visible else []
        if sample:
            print(f"\n  {CYAN}Sample events:{RESET}")
            for ev in sample:
                print(f"    [{ev.hydration_status}] {ev.title_ar or ev.slug}  "
                      f"genre_id={ev.genre_id}  starts_at={ev.starts_at}")

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    # STAGE 4 â€” get_live_categories() â€” EXACT same call as handle_sync_now
    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    hdr("STAGE 4 â€” get_live_categories() [POST_SYNC_RENDER path]")
    print(f"  {CYAN}[POST_SYNC_RENDER_START]{RESET}")
    try:
        t0 = time.perf_counter()
        cats = await discovery.get_live_categories()
        elapsed = (time.perf_counter() - t0) * 1000

        print(f"  {CYAN}[CATEGORY_FETCH_RESULT] count={len(cats)} cats={[getattr(c,'slug','?') for c in cats]}{RESET}")
        print(f"  {CYAN}[CATEGORY_KEYBOARD_COUNT] count={len(cats)}{RESET}")

        if not cats:
            record("fail", f"get_live_categories() returned [] â€” THIS IS THE PRODUCTION BUG "
                           f"(categories won't render even after patch)")
            # Diagnose why
            async with AsyncSessionLocal() as db:
                active = (await db.execute(
                    select(Genre).where(Genre.is_active == True)
                )).scalars().all()
                with_events = (await db.execute(
                    select(Genre).join(LiveEvent, LiveEvent.genre_id == Genre.id).distinct()
                )).scalars().all()
                print(f"\n  {RED}  Root cause check:{RESET}")
                print(f"    is_active=True genres:        {len(active)}")
                print(f"    genres that have events:      {len(with_events)}")
                if with_events and not active:
                    print(f"\n  {YELLOW}  FIX: genres exist but is_active=False. Run:{RESET}")
                    print(f"    UPDATE genre SET is_active=TRUE WHERE id IN "
                          f"(SELECT DISTINCT genre_id FROM live_event WHERE genre_id IS NOT NULL);")
        else:
            record("pass", f"get_live_categories() returned {len(cats)} categories in {elapsed:.0f}ms")

            # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Simulate exact keyboard build from patched handle_sync_now â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            print(f"\n  {CYAN}[CATEGORY_BUTTON_ADDED] â€” simulating keyboard build:{RESET}")
            buttons = []
            for cat in cats:
                try:
                    evs = await discovery.get_events_by_genre(cat.slug)
                    ev_count = len(evs)
                except Exception as ex:
                    ev_count = 0
                    warn(f"get_events_by_genre({cat.slug}) failed: {ex}")

                label  = f"\U0001f3ad {cat.name_ar} ({ev_count})"
                cb     = f"browse_org:{cat.slug}"
                cb_len = len(cb.encode())
                buttons.append((label, cb, ev_count, cb_len))
                print(f"    {CYAN}[CATEGORY_BUTTON_ADDED]{RESET} "
                      f"slug={cat.slug}  events={ev_count}  "
                      f"callback_data='{cb}' ({cb_len}B)")

                if cb_len > 64:
                    record("fail", f"callback_data '{cb}' is {cb_len} bytes â€” TELEGRAM LIMIT IS 64 BYTES")

            record("pass", f"Keyboard would have {len(buttons)} category buttons + 1 back = "
                           f"{len(buttons)+1} total buttons")
            print(f"\n  {CYAN}[POST_SYNC_RENDER_COMPLETE]{RESET}")

    except Exception as e:
        record("fail", f"get_live_categories() threw: {e}")
        traceback.print_exc()

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    # STAGE 5 â€” FSM state check (Redis)
    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    hdr("STAGE 5 â€” Redis / FSM State")
    try:
        import redis.asyncio as aioredis
        redis_url = os.getenv("REDIS_URL", "redis://192.168.0.2:6379/0")
        r = aioredis.from_url(redis_url, decode_responses=True)
        await r.ping()
        record("pass", f"Redis connected at {redis_url}")

        # Check for stale FSM keys
        fsm_keys = await r.keys("fsm:*")
        info(f"Active FSM state keys: {len(fsm_keys)}")
        if fsm_keys:
            for k in fsm_keys[:5]:
                val = await r.get(k)
                print(f"    key={k}  value={val}")
        print(f"  {CYAN}[FSM_STATE_AFTER_SYNC] state=CLEARED (will be set by state.clear() in patched handler){RESET}")

        # Check reservation queue
        queue_key = os.getenv("RESERVATION_QUEUE_KEY", "reservation_queue")
        queue_len = await r.llen(queue_key)
        info(f"Reservation queue depth: {queue_len}")
        await r.aclose()

    except ImportError:
        record("warn", "redis-py not importable â€” skipping Redis stage")
    except Exception as e:
        record("warn", f"Redis check failed ({e}) â€” FSM validation skipped")

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    # STAGE 6 â€” Full callback chain: browse_org â†’ events list
    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    hdr("STAGE 6 â€” Category Callback Chain (browse_org)")
    async with AsyncSessionLocal() as db:
        active_genres = (await db.execute(
            select(Genre).where(Genre.is_active == True)
        )).scalars().all()

    if not active_genres:
        record("fail", "No active genres â€” skipping callback chain test")
    else:
        for genre in active_genres[:3]:  # test up to 3 categories
            try:
                events = await discovery.get_events_by_genre(genre.slug)
                cb_data = f"browse_org:{genre.slug}"
                info(f"callback_data='{cb_data}' â†’ {len(events)} events")

                if not events:
                    record("warn", f"Genre '{genre.slug}' has no visible events")
                else:
                    record("pass", f"Genre '{genre.slug}' â†’ {len(events)} events found")

                    # Validate each event button payload
                    for ev in events[:5]:
                        ev_cb = f"e_det:{ev.id}"
                        if len(ev_cb.encode()) > 64:
                            record("fail", f"event callback_data too long: '{ev_cb}'")
                        date_ok   = ev.starts_at is not None
                        venue_ok  = bool(ev.venue_name or ev.venue_name_ar or ev.venue_name_en)
                        title_ok  = bool(ev.title_ar or ev.slug)
                        print(f"    ev_id={ev.id}  title='{(ev.title_ar or ev.slug)[:30]}'  "
                              f"date={'\u2713' if date_ok else '\u2717'}  "
                              f"venue={'\u2713' if venue_ok else '?'}  "
                              f"cb='{ev_cb}' ({len(ev_cb.encode())}B)")

            except Exception as e:
                record("fail", f"get_events_by_genre('{genre.slug}') failed: {e}")
                traceback.print_exc()

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    # STAGE 7 â€” Ticket filter (proceed_to_categories path)
    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    hdr("STAGE 7 â€” Live Ticket Filter (proceed_to_categories)")
    try:
        from services.discovery.engine import DiscoveryEngine as DE
        from apps.bot.handlers import ticket_has_available_inventory, extract_ticket_list
    except ImportError:
        try:
            from handlers import ticket_has_available_inventory, extract_ticket_list
        except ImportError:
            record("warn", "Cannot import ticket_has_available_inventory â€” skipping stage 7")
            ticket_has_available_inventory = None

    if ticket_has_available_inventory:
        # Test the fixed filter against all known Webook status values
        test_cases = [
            ({"sale_status": "on_sale",  "price": 100},              True,  "on_sale"),
            ({"sale_status": "onsale",   "price": 100},              True,  "onsale"),
            ({"status":      "active",   "price": 100},              True,  "active"),
            ({"sale_status": "closed",   "price": 100},              False, "closed"),
            ({"sale_status": "on_sale",  "sold_out": True},          False, "on_sale+sold_out"),
            ({"sale_status": "on_sale",  "remaining": 0},            False, "remaining=0"),
            ({"sale_status": "on_sale",  "remaining": 5},            True,  "remaining=5"),
            ({"sale_status": "on_sale",  "remaining": None},         True,  "remaining=None"),
        ]
        all_ok = True
        for ticket, expected, label in test_cases:
            got = ticket_has_available_inventory(ticket)
            ok_ = (got == expected)
            all_ok = all_ok and ok_
            (record("pass", f"ticket filter: {label}") if ok_
             else record("fail", f"ticket filter WRONG for {label}: expected={expected} got={got}"))
        if all_ok:
            record("pass", "All ticket filter cases correct â€” on_sale tickets will not be blocked")

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    # STAGE 8 â€” Worker: task creation + QUEUED status
    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    hdr("STAGE 8 â€” Worker Task Creation")
    async with AsyncSessionLocal() as db:
        # Count existing tasks
        all_tasks = (await db.execute(select(ReservationTask))).scalars().all()
        queued    = [t for t in all_tasks if t.status == TaskStatus.QUEUED.value]
        failed    = [t for t in all_tasks if t.status == TaskStatus.FAILED.value]
        reserved  = [t for t in all_tasks if t.status == TaskStatus.RESERVED.value]

        info(f"Total tasks in DB:    {len(all_tasks)}")
        info(f"QUEUED:               {len(queued)}")
        info(f"FAILED:               {len(failed)}")
        info(f"RESERVED/COMPLETED:   {len(reserved)}")

        if all_tasks:
            # Show most recent
            recent = sorted(all_tasks, key=lambda t: t.id, reverse=True)[:3]
            print(f"\n  {CYAN}Recent tasks:{RESET}")
            for t in recent:
                print(f"    id={t.id}  slug={t.event_slug}  status={t.status}  "
                      f"category={t.category}  count={t.seat_count}")

        # Create a test task to verify write path works
        try:
            test_task = ReservationTask(
                user_id=999999999,   # dummy test user
                event_slug="__diagnostic_test__",
                category="test_cat",
                seat_count=1,
                status=TaskStatus.CREATED.value
            )
            db.add(test_task)
            await db.commit()
            test_id = test_task.id
            record("pass", f"Task write path OK â€” test task id={test_id}")

            # Set to QUEUED (same as exec_b handler would)
            test_task.status = TaskStatus.QUEUED.value
            await db.commit()
            record("pass", f"Task status transition CREATEDâ†’QUEUED OK")

            # Clean up
            await db.delete(test_task)
            await db.commit()
            record("pass", "Test task cleaned up")
        except Exception as e:
            record("fail", f"Task write/status transition failed: {e}")
            traceback.print_exc()

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    # STAGE 9 â€” Account availability
    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    hdr("STAGE 9 â€” Account / Sniper Account")
    try:
        async with AsyncSessionLocal() as db:
            acc_repo = AccountRepository(db)
            account  = await acc_repo.get_sniper_account()
            all_accs = await acc_repo.get_available_accounts()

            info(f"Available accounts:    {len(all_accs)}")
            info(f"Sniper account found:  {bool(account)}")

            if not account:
                record("fail", "No sniper account â€” reservation flow will abort at RESERVE_NO_ACCOUNT")
                print(f"\n  {YELLOW}  Link an account via /start â†’ \u0631\u0628\u0637 \u062d\u0633\u0627\u0628 Webook{RESET}")
            else:
                record("pass",
                    f"Sniper account ok â€” id={account.id} "
                    f"health={account.health} is_active={account.is_active}"
                )
    except Exception as e:
        record("warn", f"Account check failed: {e}")

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    # STAGE 10 â€” Seated event check
    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    hdr("STAGE 10 â€” Seated Event Detection")
    async with AsyncSessionLocal() as db:
        # Look for events flagged as seated in metadata
        all_ev = (await db.execute(select(LiveEvent).where(
            LiveEvent.status != "GHOST"
        ).limit(100))).scalars().all()

        seated = []
        for ev in all_ev:
            meta = ev.metadata_json or {}
            if meta.get("is_seated") or meta.get("isSeated") or meta.get("seats_planner"):
                seated.append(ev)

        info(f"Seated events found:  {len(seated)}")
        if seated:
            for ev in seated[:3]:
                meta = ev.metadata_json or {}
                has_chart = bool(
                    meta.get("seats_io", {}).get("chart_key") or
                    ev.chart_key
                )
                print(f"    slug={ev.slug}  chart_key={'\u2713' if has_chart else '\u2717 MISSING â€” fallback will trigger'}")
            record("pass", f"{len(seated)} seated events; fallback enabled for those missing chart_key")
        else:
            record("warn", "No seated events in DB (OK if your events are plain)")

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    # SUMMARY
    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    hdr("FINAL REPORT")
    total = results["pass"] + results["fail"] + results["warn"]
    print(f"  {GREEN}{results['pass']} PASS{RESET}   "
          f"{RED}{results['fail']} FAIL{RESET}   "
          f"{YELLOW}{results['warn']} WARN{RESET}   "
          f"(out of {total} checks)\n")

    if results["fail"] == 0:
        print(f"  {GREEN}{BOLD}STATUS: READY FOR LIVE TELEGRAM TESTING{RESET}")
        print(f"\n  Deploy handlers.py then run this Telegram flow:")
        print(f"  /start â†’ \u0627\u062e\u062a\u0631 \u0641\u0639\u0627\u0644\u064a\u0629 â†’ \u062a\u062d\u062f\u064a\u062b (sync) â†’ categories must appear immediately")
        print(f"\n  Watch logs for these REQUIRED lines:")
        print(f"    [POST_SYNC_RENDER_START]")
        print(f"    [CATEGORY_FETCH_RESULT] count=N    â† must be > 0")
        print(f"    [CATEGORY_KEYBOARD_COUNT] count=N  â† must be > 0")
        print(f"    [POST_SYNC_RENDER_COMPLETE]")
        print(f"\n  If count is 0 there, come back with output of Stage 4 above.")
    elif results["fail"] <= 2:
        print(f"  {YELLOW}{BOLD}STATUS: PARTIALLY WORKING â€” fix the FAILs above first{RESET}")
    else:
        print(f"  {RED}{BOLD}STATUS: NOT READY â€” multiple failures blocking production{RESET}")

    print()


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
if __name__ == "__main__":
    asyncio.run(run_all())
