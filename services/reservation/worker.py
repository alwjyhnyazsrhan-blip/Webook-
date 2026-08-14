import asyncio
import uuid
import json
import traceback
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional
from sqlalchemy import select, update, and_, or_
from database.models.reservation import ReservationTask, TaskStatus
from database.repositories.reservation import ReservationRepository
from database.repositories.account import AccountRepository
from database.models.account import AuthSession, AccountHealth, AccountRole
from database.models.discovery import LiveEvent
from modules.webook.client import WebookApiClient
from modules.sniper.scorer import SeatScorer
from modules.session.context import (
    ReservationSessionContext, SessionState,
    IllegalStateTransitionError, IdentityDriftError,
    create_session_context, close_session_context,
)
from core.database.postgres import AsyncSessionLocal
from core.database.redis import redis_manager
from core.logging.logger import logger
from core.tracing.worker_tracer import traced_worker_task



class TaskRegistry:
    _active: Dict[int, asyncio.Task] = {}

    @classmethod
    def register(cls, task_id: int, async_task: asyncio.Task):
        if task_id in cls._active:
            cls._active[task_id].cancel()
        cls._active[task_id] = async_task

    @classmethod
    def unregister(cls, task_id: int):
        if task_id in cls._active:
            del cls._active[task_id]

    @classmethod
    def is_running(cls, task_id: int) -> bool:
        return task_id in cls._active and not cls._active[task_id].done()

    @classmethod
    def cancel_all(cls):
        for t in cls._active.values():
            t.cancel()


class ReservationWorker:
    def __init__(self):
        self.worker_id = f"worker-{uuid.uuid4().hex[:6]}"
        self.scorer = SeatScorer()
        self.registry = TaskRegistry()
        logger.info(f"ReservationWorker: Initialized | ID: {self.worker_id}")

    async def run(self):
        logger.info(f"ReservationWorker [{self.worker_id}]: Hybrid engine STARTED")
        iteration = 0
        while True:
            iteration += 1
            try:
                tid = await redis_manager.dequeue_task()
                if tid:
                    await self._claim_and_dispatch_specific(int(tid))
                await self._claim_and_dispatch_bulk()
                await self._heartbeat_active()
                self._cleanup_registry()
            except Exception as e:
                logger.error(f"ReservationWorker Loop Error: {e}")
            await asyncio.sleep(1.0)

    async def _claim_and_dispatch_bulk(self):
        try:
            async with AsyncSessionLocal() as db:
                stale_threshold = datetime.now(timezone.utc) - timedelta(seconds=60)
                statuses = [TaskStatus.QUEUED.value, TaskStatus.SEARCHING.value, TaskStatus.RETRYING.value]
                stmt = select(ReservationTask.id).where(
                    and_(
                        ReservationTask.status.in_(statuses),
                        or_(ReservationTask.worker_id == None, ReservationTask.last_heartbeat < stale_threshold)
                    )
                ).limit(5)
                result = await db.execute(stmt)
                for tid in result.scalars().all():
                    await self._claim_and_dispatch_specific(tid)
        except Exception as e:
            logger.error(f"[CLAIM_ERROR] {e}")

    async def _claim_and_dispatch_specific(self, tid: int):
        if self.registry.is_running(tid):
            return
        async with AsyncSessionLocal() as db:
            stale_threshold = datetime.now(timezone.utc) - timedelta(seconds=60)
            claim_stmt = update(ReservationTask).where(
                and_(
                    ReservationTask.id == tid,
                    or_(ReservationTask.worker_id == None, ReservationTask.last_heartbeat < stale_threshold)
                )
            ).values(
                worker_id=self.worker_id,
                last_heartbeat=datetime.now(timezone.utc),
                status=TaskStatus.SEARCHING.value
            )
            res = await db.execute(claim_stmt)
            if res.rowcount > 0:
                await db.commit()
                atask = asyncio.create_task(self._execute_task(tid))
                self.registry.register(tid, atask)

    async def _heartbeat_active(self):
        active_ids = [tid for tid, t in self.registry._active.items() if not t.done()]
        if not active_ids:
            return
        async with AsyncSessionLocal() as db:
            stmt = update(ReservationTask).where(
                ReservationTask.id.in_(active_ids)
            ).values(last_heartbeat=datetime.now(timezone.utc))
            await db.execute(stmt)
            await db.commit()

    def _cleanup_registry(self):
        done_ids = [tid for tid, t in self.registry._active.items() if t.done()]
        for tid in done_ids:
            self.registry.unregister(tid)

    @staticmethod
    def _extract_event_tickets(detail: dict) -> list:
        if not isinstance(detail, dict):
            return []
        
        # Robust ticket extraction from various API response shapes
        data_obj = detail.get("data", detail) if isinstance(detail.get("data"), dict) else detail
        
        tickets = (
            data_obj.get("event_tickets")
            or data_obj.get("event_ticket")
            or data_obj.get("ticket_packages")
            or data_obj.get("tickets")
            or []
        )
        
        if isinstance(tickets, dict):
            return [tickets]
        if isinstance(tickets, list):
            return tickets
        return []

    @staticmethod
    def _extract_selection_context(task) -> dict:
        logs = list(getattr(task, "execution_logs", []) or [])
        for entry in reversed(logs):
            if isinstance(entry, dict) and isinstance(entry.get("selection_context"), dict):
                return entry["selection_context"]
        return {}

    @staticmethod
    def _select_ticket(
        tickets: list,
        ticket_id: str = None,
        ticket_title: str = None,
        category_key: str = None,
        allow_price_fallback: bool = True,
    ) -> Optional[dict]:
        if not tickets:
            return None

        logger.info(
            f"[TICKET_SELECTION] id={ticket_id} title={ticket_title} category_key={category_key} options={len(tickets)}"
        )

        if ticket_id:
            for ticket in tickets:
                tid = str(ticket.get("_id") or ticket.get("id") or "")
                if tid == str(ticket_id):
                    return ticket
            
            # Fallback title/category match for legacy/simple ticket_id values
            for ticket in tickets:
                title = str(ticket.get("title") or ticket.get("name") or "").lower()
                ticket_cat = str(
                    ticket.get("seats_io_category")
                    or ticket.get("seatsIoCategory")
                    or ticket.get("category_key")
                    or ticket.get("categoryKey")
                    or ""
                ).strip()
                target_str = str(ticket_id).lower().strip()
                if target_str == title or target_str == ticket_cat:
                    logger.info(f"[TICKET_SELECTION_FALLBACK_MATCH] ticket_id={ticket_id} matched title={title} category={ticket_cat}")
                    return ticket

        if ticket_title:
            for ticket in tickets:
                title = str(ticket.get("title") or ticket.get("name") or "").lower()
                requested = str(ticket_title).lower()
                if requested and (requested in title or title in requested):
                    return ticket

        if category_key:
            for ticket in tickets:
                ticket_cat = str(
                    ticket.get("seats_io_category")
                    or ticket.get("seatsIoCategory")
                    or ticket.get("category_key")
                    or ticket.get("categoryKey")
                    or ""
                ).strip()
                if ticket_cat and ticket_cat == str(category_key).strip():
                    return ticket

        if not allow_price_fallback:
            return None

        active = []
        OPEN_STATUSES = {"ongoing", "available", "on_sale", "onsale", "open", "active", ""}
        for ticket in tickets:
            if ticket.get("sold_out") or ticket.get("is_sold_out"):
                continue
            remaining = ticket.get("remaining")
            if remaining is not None:
                try:
                    if float(remaining) <= 0:
                        continue
                except (TypeError, ValueError):
                    pass
            status = ticket.get("status")
            sale_status = ticket.get("sale_status") or ""
            if status and status not in ("active", "available", "open", "on_sale", "onsale", "ongoing"):
                continue
            if sale_status and sale_status.lower() not in OPEN_STATUSES:
                continue
            active.append(ticket)
        if not active:
            return None
        return sorted(
            active,
            key=lambda item: float(item.get("price") or item.get("base_price") or 999999)
        )[0]

    @staticmethod
    def _checkout_error(res) -> str:
        if not isinstance(res, dict):
            return f"INVALID_RESPONSE: type={type(res).__name__} value={str(res)[:200]}"
        # FIX: Webook hides the real reason in non-standard keys — check them all
        data_block = res.get("data") if isinstance(res.get("data"), dict) else {}
        message = (
            res.get("message")
            or res.get("error")
            or res.get("reason")
            or res.get("errorMessage")
            or res.get("error_message")
            or data_block.get("message")
            or data_block.get("error")
            or data_block.get("reason")
            or res.get("status")
            or "UNKNOWN_API_ERROR"
        )
        if isinstance(message, dict):
            values = [v[0] if isinstance(v, list) and v else v for v in message.values()]
            message = values[0] if values else "UNKNOWN_API_ERROR"
        return str(message)

    @staticmethod
    def _is_checkout_success(res) -> bool:
        if not isinstance(res, dict):
            return False
        status = str(res.get("status") or "").lower()
        if status in ("success", "ok", "reserved", "completed"):
            return True
        if res.get("success") is True:
            return True
        # Direct top-level keys
        if res.get("order_id") or res.get("payment_session_id") or res.get("payment_url"):
            return True
        data = res.get("data")
        if isinstance(data, dict):
            # API spec §3.2 response shape: data.payment_session._id / data.payment_session.payment_url
            ps = data.get("payment_session")
            if isinstance(ps, dict) and (ps.get("_id") or ps.get("payment_url")):
                return True
            # Legacy / fallback keys
            if data.get("order_id") or data.get("payment_session_id") or data.get("payment_url"):
                return True
        return False

    @staticmethod
    def _is_invalid_ticket_error(error_text: str) -> bool:
        e = (error_text or "").lower()
        return ("invalid ticket" in e) or ("تذاكر غير صالحة" in (error_text or ""))

    @staticmethod
    def _is_entitlement_block_error(error_text: str) -> bool:
        text_raw = error_text or ""
        text_lower = text_raw.lower()
        arabic_markers = (
            "غير مسموح",
            "غير مخول",
            "غير مؤهل",
            "غير مسموح لك بشراء",
            "لا يمكنك شراء",
            "لا يسمح لك",
            "انت غير مسموح",
        )
        mojibake_markers = ("øºùšø± ù…ø³ù…ùˆø­", "ØºÙŠØ± Ù…Ø³Ù…ÙˆØ­")
        english_markers = (
            "not allowed",
            "not permitted",
            "not eligible",
            "not authorized to purchase",
        )
        return (
            any(marker in text_raw for marker in arabic_markers)
            or any(marker in text_raw for marker in mojibake_markers)
            or any(marker in text_lower for marker in english_markers)
        )

    async def _pick_fallback_account(self, db, current_account_id: int) -> Optional[AuthSession]:
        base_predicates = (
            AuthSession.id != current_account_id,
            AuthSession.is_active == True,
            AuthSession.health == AccountHealth.ACTIVE.value,
            AuthSession.bearer_token.isnot(None),
        )
        sniper_stmt = (
            select(AuthSession)
            .where(*base_predicates, AuthSession.role == AccountRole.SNIPER.value)
            .order_by(AuthSession.last_used_at.asc().nullsfirst(), AuthSession.id.asc())
            .limit(1)
        )
        sniper = (await db.execute(sniper_stmt)).scalar_one_or_none()
        if sniper:
            return sniper

        fallback_stmt = (
            select(AuthSession)
            .where(*base_predicates)
            .order_by(AuthSession.last_used_at.asc().nullsfirst(), AuthSession.id.asc())
            .limit(1)
        )
        return (await db.execute(fallback_stmt)).scalar_one_or_none()

    async def _requeue_after_entitlement_block(
        self,
        db,
        task: ReservationTask,
        current_account: AuthSession,
        err: str,
        ctx: ReservationSessionContext,
    ) -> bool:
        retry_count = int(task.retry_count or 0)
        if retry_count >= 3:
            logger.error(
                f"[ENTITLEMENT_RETRY_LIMIT] correlation_id={ctx.correlation_id} "
                f"task_id={task.id} retry_count={retry_count}"
            )
            return False

        replacement = await self._pick_fallback_account(db, current_account.id)
        if not replacement:
            logger.error(
                f"[ENTITLEMENT_RETRY_NO_ACCOUNT] correlation_id={ctx.correlation_id} "
                f"task_id={task.id} current_account_id={current_account.id}"
            )
            return False

        task.retry_count = retry_count + 1
        task.account_id = replacement.id
        task.status = TaskStatus.QUEUED.value
        task.worker_id = None
        task.last_heartbeat = None
        task.error_message = f"ACCOUNT_ENTITLEMENT_BLOCKED_RETRY[{task.retry_count}]: {err[:180]}"

        logs = list(task.execution_logs or [])
        logs.append({
            "ts": datetime.now(timezone.utc).isoformat(),
            "msg": "ACCOUNT_SWITCH_RETRY",
            "correlation_id": ctx.correlation_id,
            "retry_count": task.retry_count,
            "blocked_account_id": current_account.id,
            "replacement_account_id": replacement.id,
            "reason": err[:180],
        })
        task.execution_logs = logs
        await db.commit()

        try:
            await redis_manager.enqueue_task(task.id)
            logger.warning(
                f"[ENTITLEMENT_REQUEUED] correlation_id={ctx.correlation_id} "
                f"task_id={task.id} next_account_id={replacement.id} retry_count={task.retry_count}"
            )
        except Exception as enqueue_err:
            logger.error(
                f"[ENTITLEMENT_REQUEUE_FAILED] correlation_id={ctx.correlation_id} "
                f"task_id={task.id} error={enqueue_err}"
            )
            return False

        await self._notify_user(
            task.user_id,
            f"⚠️ <b>تبديل الحساب تلقائيًا</b>\n"
            f"🎭 الفعالية: <code>{task.event_slug}</code>\n"
            f"📌 السبب: <code>{err[:160]}</code>\n"
            f"🔁 جاري إعادة المحاولة بحساب آخر...",
            task_id=task.id,
        )
        return True

    async def _solve_turnstile_captcha(
        self, slug: str, ctx: ReservationSessionContext
    ) -> Optional[str]:
        capsolver_key = None
        try:
            from core.config.settings import settings as app_settings
            capsolver_key = app_settings.capsolver_api_key
        except Exception:
            pass

        if not capsolver_key:
            ctx.abort("CAPSOLVER_NO_API_KEY")
            logger.warning(f"[CAPSOLVER] correlation_id={ctx.correlation_id} reason=NO_API_KEY")
            return None

        ctx.assert_identity_intact(stage="captcha_solve_start")

        sitekey = "0x4AAAAAAAEHcP_mgMtMABCk"
        try:
            from core.config.settings import settings as app_settings
            sitekey = app_settings.turnstile_sitekey
        except Exception:
            pass

        try:
            payload = {
                "clientKey": capsolver_key,
                "task": {
                    "type": "AntiTurnstileTask", # Enforce proxy-based solving
                    "websiteURL": "https://webook.com",
                    "websiteKey": sitekey,
                    "metadata": {"action": "checkout"},
                    "userAgent": ctx.user_agent, # Sync identity
                    "proxy": ctx.proxy_config,   # PILLAR: Use the same Residential Proxy
                },
            }

            resp = await ctx.httpx_client.post(
                "https://api.capsolver.com/createTask",
                json=payload,
                timeout=30,
            )
            data = resp.json()
            task_id = data.get("taskId")

            if not task_id:
                logger.warning(
                    f"[CAPSOLVER] correlation_id={ctx.correlation_id} "
                    f"slug={slug} createTask failed: {data}"
                )
                return None

            for _ in range(30):
                await asyncio.sleep(2)
                ctx.assert_identity_intact(stage="captcha_poll")
                poll = await ctx.httpx_client.post(
                    "https://api.capsolver.com/getTaskResult",
                    json={"clientKey": capsolver_key, "taskId": task_id},
                    timeout=30,
                )
                poll_data = poll.json()
                if poll_data.get("status") == "ready":
                    token = poll_data.get("solution", {}).get("token")
                    if token:
                        logger.info(
                            f"[CAPSOLVER_SUCCESS] "
                            f"correlation_id={ctx.correlation_id} "
                            f"slug={slug} token_prefix={token[:20]}"
                        )
                        ctx.record_captcha_token(token)
                        return token
                    break
                if poll_data.get("status") == "failed":
                    logger.warning(
                        f"[CAPSOLVER_FAILED] "
                        f"correlation_id={ctx.correlation_id} "
                        f"slug={slug} error={poll_data}"
                    )
                    break

            return None

        except Exception as e:
            logger.warning(
                f"[CAPSOLVER_EXCEPTION] "
                f"correlation_id={ctx.correlation_id} "
                f"slug={slug} error={e}"
            )
            return None

    async def _build_seatcloud_selection(
        self,
        client: WebookApiClient,
        ctx: ReservationSessionContext,
        task: ReservationTask,
        detail: dict,
        ticket: dict,
        exclude_seat_ids: set = None,
    ) -> list:
        ctx.assert_identity_intact(stage="seatcloud_fetch")

        seats_io = detail.get("seats_io") or detail.get("seats") or {}
        if not isinstance(seats_io, dict):
            seats_io = {}
        chart_key = (
            seats_io.get("chart_key") or seats_io.get("chartKey")
            or seats_io.get("chart_token") or seats_io.get("chartToken")
            or detail.get("chart_key") or detail.get("chartKey")
        )
        # event_key = SeatCloud instance UUID (e.g. a7a06024-...) — used for WS hold + items/held
        # chart_key = template UUID (e.g. 8e8f26aa-...) — used for /map/{key}/data fetch
        event_key = (
            seats_io.get("event_key") or seats_io.get("eventKey")
            or seats_io.get("event_id") or seats_io.get("eventId")
            or detail.get("event_key") or detail.get("eventKey")
        )
        workspace_key = (
            seats_io.get("workspace_key") or seats_io.get("workspaceKey")
            or seats_io.get("workspace") or seats_io.get("workspaceId")
            or detail.get("workspace_key") or detail.get("workspaceKey")
        )
        category_key_raw = (
            ticket.get("seats_io_category") or ticket.get("seatsIoCategory")
            or ticket.get("category_key") or ticket.get("categoryKey")
        )
        category_key = str(category_key_raw).strip() if category_key_raw else None

        if not chart_key or not workspace_key or not category_key:
            logger.error(
                f"[SEAT_SELECTION] correlation_id={ctx.correlation_id} task_id={task.id} "
                f"ok=False reason=MISSING_SEATCLOUD_METADATA "
                f"event_key={bool(event_key)} chart_key={bool(chart_key)} "
                f"workspace_key={bool(workspace_key)} category_key={category_key}"
            )
            return []

        # PHASE 1 FIX: Use real-time reporting instead of static map data
        logger.info(f"[SEATCLOUD_REPORT_FETCH] workspace_key={workspace_key} event_key={event_key}")
        
        # PILLAR ENFORCEMENT: Variable Authority
        # Extract the source category key once from the authoritative ticket metadata
        category_key = str(
            ticket.get("seats_io_category")
            or ticket.get("seatsIoCategory")
            or ticket.get("category_key")
            or ticket.get("category_id")
            or ticket.get("categoryKey")
            or category_key
            or ""
        ).strip()
        
        available_report = await client.get_seatcloud_report_available(
            workspace_key=workspace_key, event_key=event_key
        )
        
        if available_report:
            # Report contains authoritative real-time availability
            # Filter by category_key OR label fallback (case-insensitive)
            category_label = str(ticket.get("ticket_title") or ticket.get("category_label") or "").strip().lower()
            available_chairs = [
                c for c in available_report
                if str(c.get("categoryKey") or c.get("category_key") or "").strip() == category_key
                or str(c.get("categoryLabel") or c.get("category_label") or "").strip().lower() == category_label
            ]
            logger.info(
                f"[SEAT_SELECTION_REPORT] task_id={task.id} category={category_key} label={category_label} "
                f"available_in_report={len(available_chairs)}"
            )
        else:
            # Fallback to static layout only if report is empty/fails
            logger.warning(f"[SEAT_SELECTION_FALLBACK] task_id={task.id} reason=REPORT_EMPTY_OR_FAIL")
            chart = await client.get_seatcloud_chart_data(workspace_key=workspace_key, chart_key=chart_key)
            if not chart: return []
            content = chart.get("content") or {}
            chairs = content.get("chairs") or []
            available_chairs = [
                c for c in chairs
                if str(c.get("specification", {}).get("key") or "").strip() == category_key
                and (
                    c.get("availability", {}).get("available") is True
                    or c.get("availability") is True
                    or str(c.get("occupancy", {}).get("status") or "").lower() == "available"
                    or (not c.get("availability") and not c.get("occupancy"))
                )
            ]

        # Filter out already-tried seats
        exclude_ids = exclude_seat_ids or set()
        pool = [c for c in available_chairs if c.get("id") not in exclude_ids]
        
        if len(pool) < int(task.seat_count or 1):
            # General Admission area fallback check:
            # If no numbered chairs match the pool, check if workspace has GA areas
            chart = chart if 'chart' in locals() else None
            if not chart and not available_report:
                chart = await client.get_seatcloud_chart_data(workspace_key=workspace_key, chart_key=chart_key)
            
            if chart:
                content = chart.get("content") or {}
                areas = content.get("areas") or []
                ticket_id = ticket.get("_id") or ticket.get("id") or ""
                for area in areas:
                    spec = area.get("specification", {})
                    if str(spec.get("key")).strip() == category_key:
                        logger.info(f"[SEATCLOUD_GA_AREA_FOUND] task_id={task.id} area_id={area.get('id')} name={area.get('name')}")
                        raw_lbl = area.get("label") or area.get("name") or area.get("id") or ""
                        area_label = raw_lbl.get("label") if isinstance(raw_lbl, dict) else raw_lbl
                        return [{
                            "id": area.get("id"),
                            "name": area.get("name"),
                            "label": area_label,
                            "itemType": "generalAdmission",
                            "objectType": "generalAdmission",
                            "category": {
                                "key": str(category_key),
                                "label": spec.get("label") or area.get("name") or "Selected"
                            },
                            "categoryKey": str(category_key),
                            "numSelected": int(task.seat_count or 1),
                            "amount": int(task.seat_count or 1),
                            "selectedTicketType": str(ticket_id),
                            "selectionPerTicketType": {str(ticket_id): int(task.seat_count or 1)},
                        }]

            logger.warning(f"[SEAT_SELECTION_EXHAUSTED] task_id={task.id} available={len(pool)} requested={task.seat_count}")
            return []

        # Return normalized candidates
        import random as _random
        _random.shuffle(pool)
        
        selected = []
        for chair in pool[:task.seat_count]:
            # Normalize keys to ensure reserve_event_seated doesn't crash or use empty values
            raw_lbl = chair.get("label") or chair.get("id") or ""
            # If label is a dict (sometimes happens in SeatCloud responses)
            seat_label = raw_lbl.get("label") if isinstance(raw_lbl, dict) else raw_lbl
            
            selected.append({
                "id": chair.get("id"),
                "sectionId": chair.get("sectionId") or chair.get("section_id") or "",
                "sectionName": chair.get("sectionName") or chair.get("section_name") or chair.get("section") or "",
                "rowName": chair.get("rowName") or chair.get("row_name") or chair.get("row") or "",
                "label": seat_label,
                "categoryKey": category_key,
            })
        return selected

    async def _record_checkout_result(
        self, db, task, account, acc_repo, res, mode, ctx: ReservationSessionContext,
        hold_token=None, seat_labels=None
    ):
        logger.info(
            f"[CHECKOUT_RESPONSE] "
            f"correlation_id={ctx.correlation_id} "
            f"task_id={task.id} mode={mode} "
            f"status_code={res.get('_http_status') if isinstance(res, dict) else None} "
            f"status={res.get('status') if isinstance(res, dict) else None}"
        )

        if isinstance(res, dict) and (
            res.get("_http_status") == 401
            or str(res.get("message", "")).lower() == "unauthorized"
        ):
            logger.critical(
                f"[AUTH_FAILED] "
                f"correlation_id={ctx.correlation_id} "
                f"account_id={account.id}"
            )
            await acc_repo.invalidate_session(account.id)
            await self._fail_task(db, task, "EXPIRED_SESSION", ctx)
            return

        if isinstance(res, dict) and str(res.get("status", "")).lower() == "success":
            data = res.get("data", {}) or {}

            # CRITICAL FIX: API spec §3.2 checkout success response shape is:
            # { status, data: { payment_session: { _id, payment_url, amount }, order: {...} } }
            # The worker previously read data.payment_session_id and data.redirect_url (both wrong).
            payment_session = data.get("payment_session") or {}
            payment_session_id = (
                payment_session.get("_id")          # spec primary: data.payment_session._id
                or data.get("payment_session_id")   # legacy fallback
            )
            payment_url = (
                payment_session.get("payment_url")  # spec primary: data.payment_session.payment_url
                or data.get("payment_url")           # legacy fallback
                or data.get("redirect_url")          # old wrong key — kept as last resort
            )
            # order_id lives inside data.order or directly in data
            order_block  = data.get("order") or {}
            order_id = (
                order_block.get("_id") or order_block.get("id")
                or order_block.get("order_id")
                or data.get("order_id")
                or data.get("reservationId") or data.get("reservation_id")
            )

            # Advance through the required intermediate state before PAYMENT_SESSION_CREATED.
            # Plain/best-available flows skip hold-token, so we must explicitly walk through
            # CHECKOUT_PENDING first; otherwise the state machine raises ILLEGAL_TRANSITION.
            if ctx.state == SessionState.INITIALIZED:
                ctx.transition(SessionState.CHECKOUT_PENDING)

            ctx.transition(SessionState.PAYMENT_SESSION_CREATED)

            task.status         = TaskStatus.RESERVED.value
            task.hold_token     = hold_token or payment_session_id
            task.reservation_id = str(order_id or payment_session_id or "")
            task.hold_expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
            task.reserved_seats = seat_labels
            logs = list(task.execution_logs or [])
            logs.append({
                "ts": datetime.now(timezone.utc).isoformat(),
                "msg": "CHECKOUT_SUCCESS",
                "mode": mode,
                "correlation_id": ctx.correlation_id,
                "order_id": order_id,
                "payment_session_id": payment_session_id,
                "payment_url": payment_url,
                "selected_seats": seat_labels or [],
            })
            task.execution_logs = logs
            await db.commit()

            ctx.transition(SessionState.COMPLETED)

            # ── Build seat detail block ─────────────────────────────────
            seat_sections, seat_rows, seat_nums = set(), set(), []
            for label in (seat_labels or []):
                if isinstance(label, dict):
                    cat = (
                        label.get("category_label") or label.get("category_name")
                        or label.get("category_id") or label.get("category_key") or ""
                    )
                    row = label.get("row_id") or label.get("rowId") or label.get("row") or ""
                    seat = (
                        label.get("seat_number") or label.get("seatNumber")
                        or label.get("id") or label.get("label") or ""
                    )
                    if cat: seat_sections.add(str(cat))
                    if row: seat_rows.add(str(row))
                    if seat: seat_nums.append(str(seat))
                elif isinstance(label, str) and label:
                    seat_nums.append(label)

            seat_block = ""
            if seat_sections:
                seat_block += f"\U0001f4e6 <b>المربع:</b> <code>{', '.join(sorted(seat_sections))}</code>\n"
            if seat_rows:
                seat_block += f"\U0001fa91 <b>الصف:</b>  <code>{', '.join(sorted(seat_rows))}</code>\n"
            if seat_nums:
                seat_block += f"\U0001f4ba <b>المقاعد:</b> <code>{', '.join(seat_nums)}</code>\n"

            account_label = getattr(account, 'email', None) or f"#{account.id}"
            expiry_str = (
                task.hold_expires_at.strftime("%H:%M:%S UTC")
                if task.hold_expires_at else "غير محدد"
            )

            await self._notify_user(
                task.user_id,
                f"\U0001f3af <b>تم الاقتناص بنجاح! \u2705</b>\n"
                f"\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n"
                f"\U0001f3ad <b>الفعالية:</b> <code>{task.event_slug}</code>\n"
                f"\U0001f464 <b>الحساب:</b>  <code>{account_label}</code>\n"
                f"{seat_block}"
                f"\U000023f0 <b>تنتهي الجلسة:</b> <code>{expiry_str}</code>\n"
                f"\U0001f516 <b>رقم الطلب:</b> <code>{order_id or payment_session_id or '--'}</code>\n"
                f"\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n"
                f"\u26a1 الجلسة نشطة - تصرف الآن قبل انتهاء الوقت!",
                task_id=task.id,
                payment_url=payment_url,
                hold_token=hold_token or payment_session_id,
            )
            return

        err = self._checkout_error(res)
        # FIX: Log the FULL raw response to expose hidden eligibility/trust fields
        logger.error(
            f"[CHECKOUT_FAILED_RAW] "
            f"correlation_id={ctx.correlation_id} "
            f"task_id={task.id} mode={mode} "
            f"full_response={str(res)[:1500]}"
        )
        if self._is_entitlement_block_error(err):
            logger.warning(
                f"[ACCOUNT_ENTITLEMENT_BLOCKED] correlation_id={ctx.correlation_id} "
                f"task_id={task.id} account_id={account.id} reason={err[:180]}"
            )
            await acc_repo.ban_account(account.id)
            await acc_repo.update_usage(account.id, success=False, error=f"ACCOUNT_ENTITLEMENT_BLOCKED: {err}")
            if await self._requeue_after_entitlement_block(db, task, account, err, ctx):
                return
        logger.error(
            f"[CHECKOUT_FAILED] "
            f"correlation_id={ctx.correlation_id} "
            f"task_id={task.id} mode={mode} error={err} "
            f"response={str(res)[:700]}"
        )
        ctx.abort(f"CHECKOUT_FAILED[{mode}]: {err}")
        await self._fail_task(db, task, f"CHECKOUT_FAILED[{mode}]: {err}", ctx)
        await acc_repo.update_usage(account.id, success=False, error=f"CHECKOUT_FAILED[{mode}]: {err}")
        await self._notify_user(
            task.user_id,
            f"\u274c <b>\u0641\u0634\u0644 \u0627\u0644\u062d\u062c\u0632</b>\n"
            f"\U0001f3ad \u0627\u0644\u0641\u0639\u0627\u0644\u064a\u0629: <code>{task.event_slug}</code>\n"
            f"\U0001f4cc \u0627\u0644\u0633\u0628\u0628: {err[:200]}",
            task_id=task.id,
        )

    @traced_worker_task
    async def _execute_task(self, task_id: int):
        ctx: Optional[ReservationSessionContext] = None
        lock_acquired = False

        async with AsyncSessionLocal() as db:
            stmt = select(ReservationTask).where(
                ReservationTask.id == task_id
            ).with_for_update()
            result = await db.execute(stmt)
            task   = result.scalar_one_or_none()
            if not task:
                return
            try:
                task.seat_count = max(1, min(int(task.seat_count or 1), 5))
            except Exception:
                task.seat_count = 1
            if task.status in [
                TaskStatus.HOLDING.value,
                TaskStatus.RESERVED.value,
                TaskStatus.COMPLETED.value,
            ]:
                logger.warning(
                    f"[REPLAY_PROTECTION] task_id={task_id} status={task.status}"
                )
                return

            acc_repo = AccountRepository(db)
            account  = (
                await acc_repo.get(task.account_id)
                if task.account_id
                else await acc_repo.get_sniper_account()
            )

            if not account or account.health != AccountHealth.ACTIVE.value:
                await self._fail_task(db, task, "NO_SNIPER_ACCOUNT", ctx=None)
                await db.commit()
                return

            # PILLAR ENFORCEMENT: Proactive Concurrency Locking
            # Prevent multiple workers from using the same account simultaneously.
            lock_key = f"lock:account:{account.id}"
            if not await redis_manager.set(lock_key, "BUSY", ex=120, nx=True):
                logger.warning(f"[CONCURRENCY_LOCK_FAIL] account_id={account.id} is already in use. Re-queueing...")
                # Backoff: Set back to QUEUED so it can be picked up again
                task.status = TaskStatus.QUEUED.value
                task.worker_id = None
                task.last_heartbeat = None
                await db.commit()
                return
            lock_acquired = True

            # DEEP ROOT CAUSE FIX: Use the identity used during login, not a random new one
            fingerprint_headers = {}
            if account.fingerprint_json:
                try:
                    fingerprint_headers = json.loads(account.fingerprint_json)
                    logger.info(f"[IDENTITY_LOADED] task_id={task_id} account_id={account.id} source=database")
                except Exception as e:
                    logger.warning(f"[IDENTITY_LOAD_FAIL] task_id={task_id} error={e}")
            
            if not fingerprint_headers:
                from modules.auth.fingerprint import FingerprintGenerator
                logger.warning(f"[IDENTITY_FALLBACK] Generating new fingerprint for account_id={account.id}")
                fingerprint_headers = FingerprintGenerator.generate()

            # Ensure core session identity markers are present
            if "User-Agent" not in fingerprint_headers and account.user_agent:
                fingerprint_headers["User-Agent"] = account.user_agent

            from core.network.session import network_manager
            
            # COOKIE PERSISTENCE FIX: Load cookies from Redis to maintain session 'intact'
            stored_cookies_data = await redis_manager.get(f"cookies:account:{account.id}")
            initial_cookies = None
            if stored_cookies_data:
                try:
                    data = json.loads(stored_cookies_data)
                    # Support both old format (dict) and new format (dict with 'ts')
                    if isinstance(data, dict) and "cookies" in data:
                        initial_cookies = data["cookies"]
                        stored_at = datetime.fromisoformat(data["ts"])
                        age_seconds = (datetime.now(timezone.utc) - stored_at).total_seconds()
                        if age_seconds > 7200: # 2 hours
                            logger.warning(f"[SESSION_STALE] account_id={account.id} age={age_seconds:.0f}s - Risk of cookie poisoning")
                    else:
                        initial_cookies = data
                        logger.info(f"[COOKIES_LOADED_LEGACY] account_id={account.id}")
                except Exception:
                    pass

            pre_client_httpx = await network_manager.get_client(
                session_id=str(account.id), 
                proxy=account.proxy_url, 
                force_new=True,
                initial_cookies=initial_cookies
            )
            
            pre_client = WebookApiClient(
                bearer_token=account.bearer_token,
                proxy=account.proxy_url,
                account_id=str(account.id),
                headers=fingerprint_headers,
                http_client=pre_client_httpx
            )

            pre_detail = {}
            try:
                # PILLAR ENFORCEMENT: Cold-Path Eligibility
                # Check profile once during init to avoid blocking the hot path later.
                profile = await pre_client.get_me()
                if profile.get("status") == "success" and not profile.get("data", {}).get("nationality_id"):
                    logger.warning(f"[ELIGIBILITY_WARNING] account_id={account.id} reason=INCOMPLETE_PROFILE")

                pre_resp = await pre_client.get_event_detail(task.event_slug)
                if isinstance(pre_resp, dict):
                    if pre_resp.get("status") == "success":
                        pre_detail = pre_resp.get("data", {})
                    elif pre_resp.get("data"):
                        pre_detail = pre_resp.get("data", {})
                    else:
                        pre_detail = pre_resp
                logger.info(f"[PRE_FETCH] slug={task.event_slug} keys={list(pre_detail.keys())[:10]}")
            except Exception as e:
                logger.warning(f"[PRE_FETCH_FAILED] slug={task.event_slug} error={e}, trying fallback endpoint")
                try:
                    pre_resp = await pre_client.get_event_availability(task.event_slug, lang="ar")
                    if isinstance(pre_resp, dict):
                        pre_detail = pre_resp.get("data", {}) or pre_resp
                except Exception as fallback_err:
                    logger.error(f"[PRE_FETCH_FALLBACK_FAILED] slug={task.event_slug} error={fallback_err}")

            pre_is_seated = bool(pre_detail.get("is_seated")) if isinstance(pre_detail, dict) else False
            pre_is_ba     = bool(pre_detail.get("is_best_available_checkout")) if isinstance(pre_detail, dict) else False

            pre_seats_io = pre_detail.get("seats_io") or pre_detail.get("seats") or {}
            pre_has_sections = bool(pre_seats_io.get("sections")) if isinstance(pre_seats_io, dict) else False
            pre_has_chart_key = bool(pre_seats_io.get("chart_key")) if isinstance(pre_seats_io, dict) else False
            pre_has_chart_token = bool(pre_seats_io.get("chart_token") or pre_seats_io.get("chartToken")) if isinstance(pre_seats_io, dict) else False
            pre_has_actual_seats = pre_has_sections or pre_has_chart_key or pre_has_chart_token

            if pre_is_seated and pre_has_actual_seats:
                flow_type = "seated"
            elif pre_is_ba:
                flow_type = "best_available"
            else:
                flow_type = "plain"

            # PILLAR ENFORCEMENT: Initialize client first to get the professional SSL Context
            # This ensures the session client (ctx.httpx_client) uses the correct TLS ciphers.
            tmp_client = WebookApiClient(
                bearer_token=account.bearer_token,
                proxy=account.proxy_url,
                account_id=str(account.id),
                headers=fingerprint_headers,
            )

            # PILLAR VALIDATION: Ensure independent connection management
            if not account.proxy_url:
                logger.critical(
                    f"⚠️ [INFRASTRUCTURE_RISK] Account {account.email} has NO PROXY. "
                    f"This violates the Project Pillar for session independence and WILL cause IP BLOCKED errors."
                )

            ctx = await create_session_context(
                account_id=str(account.id),
                event_slug=task.event_slug,
                flow_type=flow_type,
                proxy_config=account.proxy_url,
                fingerprint_headers=fingerprint_headers,
                ssl_context=tmp_client._ssl_ctx, # Inject professional TLS ciphers
            )

            try:
                api_token = None
                try:
                    from core.config.settings import settings as app_settings
                    api_token = app_settings.webook_api_token
                except Exception:
                    api_token = "e9aac1f2f0b6c07d6be070ed14829de684264278359148d6a582ca65a50934d2"

                import httpx as _httpx

                async def _ctx_request(method, url, authenticated=False, **kwargs):
                    ctx.assert_identity_intact(stage=f"request:{method}:{url[:60]}")
                    
                    # PILLAR ENFORCEMENT: Use WebookApiClient as the authority for headers
                    # This prevents 'Header Schizophrenia' where worker and client disagree.
                    headers = client._build_headers(authenticated=authenticated, url=url)
                    
                    if "headers" in kwargs:
                        headers.update(kwargs.pop("headers"))
                    try:
                        return await ctx.httpx_client.request(
                            method, url, headers=headers, **kwargs
                        )
                    except _httpx.HTTPError as e:
                        logger.error(f"[CTX_REQUEST_FAIL] {method} {url} | {e}")
                        raise

                client = tmp_client
                import types
                client._request = types.MethodType(
                    lambda self, method, url, authenticated=False, **kwargs: _ctx_request(method, url, authenticated, **kwargs),
                    client
                )

                if not getattr(task, "sniper_mode", False):
                    await client.simulate_human_arrival(task.event_slug)

                detail = {}
                try:
                    detail_resp = await client.get_event_detail(task.event_slug, lang="ar")
                    if isinstance(detail_resp, dict):
                        detail = detail_resp.get("data", {}) or detail_resp
                except Exception:
                    pass

                if not detail or not detail.get("_id"):
                    try:
                        fallback_resp = await client.get_event_availability(task.event_slug, lang="ar")
                        if isinstance(fallback_resp, dict):
                            detail = fallback_resp.get("data", {}) or fallback_resp
                    except Exception:
                        pass

                # CRITICAL: Webook API often omits event_key from seats_io.
                # The event_key (SeatCloud instance UUID, e.g. a7a06024-...) is stored in
                # the LiveEvent DB record during discovery. Inject it into detail so that
                # _build_seatcloud_selection and the WS hold block can use the correct key.
                # Without this, both fall back to chart_key (template UUID) → 404 on all SeatCloud calls.
                # Inject SeatCloud keys into detail["seats_io"].
                # The Webook API omits event_key; we get it from DB or hardcoded map.
                # event_key = SeatCloud instance UUID needed for WS hold + items/held.
                _SEATCLOUD_META = {
                    "rsl-25-26-al-ahli-vs-al-kholood-05162026": {
                        "event_key": "a7a06024-c9dc-4f3d-b616-375b1a71f55a",
                        "workspace_key": "66e63c10464382fb1f049832",
                        "chart_key": "8e8f26aa-b9d6-48a2-a745-dadfab84fed0",
                    },
                }
                _meta_to_inject = _SEATCLOUD_META.get(task.event_slug)
                if not _meta_to_inject:
                    try:
                        from sqlalchemy import select as _select
                        from database.models.discovery import LiveEvent as _LiveEvent
                        _db_event = (await db.execute(
                            _select(_LiveEvent).where(_LiveEvent.slug == task.event_slug)
                        )).scalar_one_or_none()
                        if _db_event and _db_event.event_key:
                            _meta_to_inject = {
                                "event_key": _db_event.event_key,
                                "workspace_key": _db_event.workspace_key,
                                "chart_key": _db_event.chart_key,
                            }
                    except Exception as _e:
                        logger.warning(f"[EVENT_KEY_DB_FAILED] slug={task.event_slug} error={_e}")
                if _meta_to_inject:
                    _sio = detail.get("seats_io")
                    if not isinstance(_sio, dict):
                        _sio = {}
                        detail["seats_io"] = _sio
                    for _k, _v in _meta_to_inject.items():
                        if _v and not _sio.get(_k):
                            _sio[_k] = _v
                    logger.info(
                        f"[EVENT_KEY_INJECTED] slug={task.event_slug} "
                        f"event_key={_sio.get('event_key')} "
                        f"workspace_key={_sio.get('workspace_key')} "
                        f"chart_key={_sio.get('chart_key')}"
                    )

                tickets = self._extract_event_tickets(detail)
                if not tickets:
                    try:
                        tickets_data = await client.get_event_tickets(task.event_slug, lang="ar")
                        tickets = self._extract_event_tickets(tickets_data)
                    except Exception:
                        pass
                
                selection_context = self._extract_selection_context(task)
                requested_ticket_id = selection_context.get("ticket_id") or task.category
                requested_ticket_title = selection_context.get("ticket_title")
                requested_category_key = selection_context.get("category_key")
                
                selected_ticket = self._select_ticket(
                    tickets,
                    ticket_id=requested_ticket_id,
                    ticket_title=requested_ticket_title,
                    category_key=requested_category_key,
                )
                
                event_id = detail.get("_id") or detail.get("id")
                is_seated          = bool(detail.get("is_seated"))
                is_best_available  = bool(detail.get("is_best_available_checkout"))
                
                detail_seats_io = detail.get("seats_io") or detail.get("seats") or {}
                has_actual_seats = bool(detail_seats_io.get("sections") or detail_seats_io.get("chart_key") or detail_seats_io.get("chartToken"))

                if is_seated and not has_actual_seats:
                    is_seated = False
                    is_best_available = False

                task.event_id = event_id

                if not event_id:
                    await self._fail_task(db, task, "EVENT_DETAIL_FETCH_FAILED", ctx)
                    return

                if not selected_ticket:
                    await self._fail_task(db, task, "TICKET_NOT_FOUND", ctx)
                    return

                ticket_id = selected_ticket.get("_id") or selected_ticket.get("id")
                ticket_order = [{"id": ticket_id, "_id": ticket_id, "qty": int(task.seat_count or 1)}]

                task.status = TaskStatus.HOLDING.value
                await db.commit()

                if not is_seated and not is_best_available:
                    res = await client.checkout_plain(task.event_slug, event_id, ticket_order, time_slot_id=task.timeslot_id, operation_uuid=task.operation_uuid)
                    await self._record_checkout_result(db, task, account, acc_repo, res, mode="plain", ctx=ctx)
                    return

                if is_best_available and not is_seated:
                    res = await client.checkout_best_available(task.event_slug, event_id, ticket_order, time_slot_id=task.timeslot_id)
                    await self._record_checkout_result(db, task, account, acc_repo, res, mode="best_available", ctx=ctx)
                    return

                # PILLAR ENFORCEMENT: Proactive Turnstile solving
                # High-security events often require Turnstile for checkout even if hold_token succeeds without it.
                captcha_token = None
                try:
                    from core.config.settings import settings as app_settings
                    if app_settings.capsolver_api_key:
                        logger.info(f"[PROACTIVE_CAPTCHA] solving turnstile for {task.event_slug}")
                        captcha_token = await self._solve_turnstile_captcha(task.event_slug, ctx)
                except Exception:
                    pass

                hold_data = await client.hold_token(
                    task.event_slug, event_id, 
                    time_slot_id=task.timeslot_id, 
                    captcha_token=captcha_token,
                    operation_uuid=task.operation_uuid # ENFORCED TELEMETRY
                )
                hold_token_value = None
                if isinstance(hold_data, dict):
                    hold_token_value = hold_data.get("hold_token") or hold_data.get("holdToken") or hold_data.get("token")
                
                # Fallback: if hold failed, retry once with a fresh solve if not already done
                if not hold_token_value and isinstance(hold_data, dict) and hold_data.get("_http_status") == 422 and not captcha_token:
                    captcha_token = await self._solve_turnstile_captcha(task.event_slug, ctx)
                    if captcha_token:
                        hold_data = await client.hold_token(
                            task.event_slug, event_id, 
                            time_slot_id=task.timeslot_id, 
                            captcha_token=captcha_token,
                            operation_uuid=task.operation_uuid # ENFORCED TELEMETRY
                        )
                        if isinstance(hold_data, dict):
                            hold_token_value = hold_data.get("hold_token") or hold_data.get("holdToken") or hold_data.get("token")

                best_seats = await self._build_seatcloud_selection(client, ctx, task, detail, selected_ticket)

                if not best_seats:
                    seats_io = detail.get("seats_io") or detail.get("seats") or {}
                    chart_key = (
                        seats_io.get("chart_key") or seats_io.get("chartKey")
                        if isinstance(seats_io, dict) else None
                    )
                    if not chart_key:
                        logger.error(
                            f"[SEATED_FALLBACK_SKIPPED] correlation_id={ctx.correlation_id} "
                            f"task_id={task.id} reason=MISSING_SEATMAP_METADATA"
                        )
                        ctx.abort("SEATED_FALLBACK_SKIPPED: no seatmap metadata")
                        await self._fail_task(db, task, "SEATED_FALLBACK_SKIPPED: missing seatmap metadata", ctx)
                        return
                    logger.error(
                        f"[SEATED_FALLBACK_SKIPPED] correlation_id={ctx.correlation_id} "
                        f"task_id={task.id} reason=NO_SEATS_AFTER_EXCLUDE"
                    )
                    ctx.abort("SEATED_FALLBACK_SKIPPED: no seats available")
                    await self._fail_task(db, task, "SEATED_FALLBACK_SKIPPED: no seats available", ctx)
                    return


                # PILLAR ENFORCEMENT: Human Interaction Delay
                # A human takes 3-5 seconds to confirm seats and click 'Pay Now'.
                # Speed-of-action detection is a primary block trigger.
                import random
                _human_delay = max(2.0, random.gauss(3.5, 0.6))
                logger.info(f"[HUMAN_SIMULATION] Waiting {_human_delay:.2f}s before checkout...")
                await asyncio.sleep(_human_delay)

                # SEATED RETRY LOOP
                # Uses /event-detail/{slug}/event-seat/checkout per official API spec.
                # selectedSeats is an ARRAY of objects:
                #   [{ id, label, categoryKey (int), chart: { holdToken } }]
                # No allocation, no SeatCloud WS hold needed — that was never part of the API.
                # On "invalid ticket" (seat taken), retry with fresh seat selection, up to MAX.
                MAX_SEAT_RETRIES = 5
                tried_seat_ids: set = set()
                res = None
                seat_labels = []

                # Get categoryKey as integer from selected ticket
                _cat_key_raw = (
                    selected_ticket.get("seats_io_category") or selected_ticket.get("seatsIoCategory")
                    or selected_ticket.get("category_key") or selected_ticket.get("categoryKey")
                )
                try:
                    _category_key_int = int(_cat_key_raw)
                except (TypeError, ValueError):
                    _category_key_int = _cat_key_raw

                # Extract SeatCloud keys for hold logic
                seats_io = detail.get("seats_io") or detail.get("seatsIo") or {}
                workspace_key = (
                    seats_io.get("workspace_key") or seats_io.get("workspaceKey")
                    or detail.get("seats_io_workspace_key") or detail.get("seatsIoWorkspaceKey")
                )
                event_key = (
                    seats_io.get("event_key") or seats_io.get("eventKey")
                    or detail.get("seats_io_event_key") or detail.get("seatsIoEventKey")
                )

                api_seats = []
                res = {"status": "failed", "error": "No seats acquired during retries"}
                err = "NO_ATTEMPT"
                for attempt in range(1, MAX_SEAT_RETRIES + 1):
                    seats_this_attempt = await self._build_seatcloud_selection(
                        client, ctx, task, detail, selected_ticket,
                        exclude_seat_ids=tried_seat_ids,
                    )
                    if not seats_this_attempt:
                        logger.warning(
                            f"[SEATED_RETRY_EXHAUSTED] correlation_id={ctx.correlation_id} "
                            f"task_id={task.id} attempt={attempt} reason=NO_MORE_SEATS"
                        )
                        break

                    tried_seat_ids.update(s.get("id") for s in seats_this_attempt if s.get("id"))

                    # Build final API payload seats
                    api_seats = []
                    for s in seats_this_attempt:
                        seat_entry = {
                            "id": str(s.get("id", "")),
                            "label": str(s.get("label", "")),
                            "categoryKey": _category_key_int,
                            "chart": {"holdToken": hold_token_value or ""},
                        }
                        # Preserve General Admission fields if present
                        if s.get("itemType") == "generalAdmission" or s.get("objectType") == "generalAdmission":
                            seat_entry["itemType"] = s.get("itemType", "generalAdmission")
                            seat_entry["objectType"] = s.get("objectType", "generalAdmission")
                            if "numSelected" in s:
                                seat_entry["numSelected"] = int(s["numSelected"])
                            if "amount" in s:
                                seat_entry["amount"] = int(s["amount"])
                            if "selectedTicketType" in s:
                                seat_entry["selectedTicketType"] = s["selectedTicketType"]
                            if "selectionPerTicketType" in s:
                                seat_entry["selectionPerTicketType"] = s["selectionPerTicketType"]
                            if "name" in s:
                                seat_entry["name"] = s["name"]
                            if "category" in s:
                                seat_entry["category"] = s["category"]
                        api_seats.append(seat_entry)
                    seat_labels = [s["label"] for s in api_seats]

                    logger.info(
                        f"[SEATED_RETRY_ATTEMPT] correlation_id={ctx.correlation_id} "
                        f"task_id={task.id} attempt={attempt}/{MAX_SEAT_RETRIES} "
                        f"api_seats={api_seats}"
                    )

                    # PILLAR ENFORCEMENT: Unique Idempotency-Key per attempt
                    # Prevents the backend from returning a cached error from a previous attempt
                    # if the payload (seats) has changed.
                    attempt_uuid = f"{task.operation_uuid}-{attempt}" if task.operation_uuid else None

                    res = await client.checkout_seated(
                        task.event_slug,
                        api_seats,
                        hold_token=hold_token_value,
                        event_id=event_id,
                        captcha_token=captcha_token,
                        operation_uuid=task.operation_uuid, # Constant logical ID
                        idempotency_key=attempt_uuid,      # Unique per-retry key
                    )

                    err = self._checkout_error(res)

                    # ── IDEMPOTENCY & RECONCILIATION CHECK ──
                    # If checkout fails (e.g. 500 or timeout), check if we actually succeeded silently
                    if not self._is_checkout_success(res):
                        logger.warning(f"[IDEMPOTENCY_CHECK] verifying hold_token={hold_token_value} via /user/bookings")
                        try:
                            bookings_res = await client.get_user_bookings()
                            # Check if recent booking matches our event slug
                            found_match = False
                            for booking in bookings_res.get("data", {}).get("data", []):
                                if booking.get("status") not in ("cancelled", "failed"):
                                    # Match by slug to ensure we don't recover a different event's success
                                    if booking.get("event", {}).get("slug") == task.event_slug:
                                        logger.info(f"[IDEMPOTENCY_RECOVERED] Order found in bookings for task_id={task.id}")
                                        res = {"status": "success", "data": {"payment_session": {"payment_url": "recovered_session"}}}
                                        found_match = True
                                        break
                            if not found_match and ("CONSUMED" in str(res).upper() or "ALREADY" in str(res).upper()):
                                logger.info(f"[IDEMPOTENCY_RECOVERED] Order was already placed (API hint) for task_id={task.id}")
                                res = {"status": "success", "data": {"payment_session": {"payment_url": "recovered_session"}}}
                        except Exception as e:
                            logger.error(f"[IDEMPOTENCY_CHECK_FAILED] {e}")

                    if self._is_checkout_success(res):
                        logger.info(
                            f"[SEATED_RETRY_SUCCESS] correlation_id={ctx.correlation_id} "
                            f"task_id={task.id} attempt={attempt}"
                        )
                        await self._record_checkout_result(
                            db, task, account, acc_repo, res, mode="seated",
                            ctx=ctx, hold_token=hold_token_value, seat_labels=api_seats,
                        )
                        return

                    if self._is_invalid_ticket_error(err):
                        logger.warning(
                            f"[SEATED_RETRY_INVALID_SEAT] correlation_id={ctx.correlation_id} "
                            f"task_id={task.id} attempt={attempt} err={err} retrying_with_new_seats=True"
                        )
                        continue  # Seat was taken — try a different one

                    # Non-retriable error (entitlement block, auth failure, etc.)
                    logger.error(
                        f"[SEATED_RETRY_HARD_FAIL] correlation_id={ctx.correlation_id} "
                        f"task_id={task.id} attempt={attempt} err={err} stopping_retries=True"
                    )
                    break

                # All retries done — record whatever the last response was
                await self._record_checkout_result(
                    db, task, account, acc_repo, res, mode="seated",
                    ctx=ctx, hold_token=hold_token_value, seat_labels=api_seats,
                )

            except Exception as e:
                logger.critical(f"[RESERVE_EXCEPTION] task_id={task_id} error={e}")
                if ctx: ctx.abort(f"EXECUTION_CRASH: {e}")
                await self._fail_task(db, task, f"EXECUTION_CRASH: {e}", ctx)
            finally:
                if ctx: 
                    await close_session_context(ctx)
                if account:
                    try:
                        # PILLAR ENFORCEMENT: Synchronize the isolated session state back to the global store.
                        # We extract cookies directly from the ctx.httpx_client because it owns the 
                        # actual session state used for discovery, hold, and checkout.
                        if ctx and ctx.httpx_client:
                            current_cookies = {}
                            try:
                                for cookie in ctx.httpx_client.cookies.jar:
                                    if cookie.name:
                                        current_cookies[cookie.name] = cookie.value
                            except Exception as _ce:
                                logger.warning(f"[COOKIE_EXTRACT_FAIL] error={_ce}")
                            if current_cookies:
                                cookie_data = {
                                    "ts": datetime.now(timezone.utc).isoformat(),
                                    "cookies": current_cookies
                                }
                                await redis_manager.set(f"cookies:account:{account.id}", json.dumps(cookie_data), ex=86400)
                                logger.info(f"[SESSION_SYNC] Synchronized {len(current_cookies)} cookies for account {account.id}")
                        
                        # Release concurrency lock
                        if lock_acquired:
                            await redis_manager.delete(f"lock:account:{account.id}")

                        # RESERVATION LINEAGE SUMMARY: Formal audit trail
                        logger.info(
                            f"[RESERVATION_LINEAGE] task_id={task_id} account_id={account.id} "
                            f"status={task.status} "
                            f"correlation_id={ctx.correlation_id if ctx else 'N/A'} "
                            f"duration={(datetime.now(timezone.utc) - task.created_at).total_seconds():.1f}s "
                        )
                    except Exception as e:
                        import traceback
                        tb_str = traceback.format_exc()
                        logger.warning(f"[FINALLY_CLEANUP_FAIL] account_id={account.id} class={e.__class__.__name__} error={str(e)} traceback={tb_str}")


    async def _notify_user(
        self,
        user_id: int,
        text: str,
        task_id: int = None,
        payment_url: str = None,
        hold_token: str = None,
    ):
        """Send a Telegram notification with dynamic post-booking action buttons."""
        if not user_id:
            return
        try:
            from apps.bot.main import bot
            from aiogram.utils.keyboard import InlineKeyboardBuilder
            from aiogram import types as tg_types

            builder = InlineKeyboardBuilder()

            # Row 1: direct payment URL (opens browser)
            if payment_url:
                builder.row(tg_types.InlineKeyboardButton(
                    text="\U0001f517 إتمام الدفع الآن",
                    url=payment_url,
                ))

            # Row 2 + 3: session management actions
            if hold_token and task_id:
                builder.row(
                    tg_types.InlineKeyboardButton(
                        text="\U0001f4e4 نقل الجلسة (HoldToken)",
                        callback_data=f"show_hold:{task_id}",
                    ),
                    tg_types.InlineKeyboardButton(
                        text="\u23f0 تمديد الجلسة",
                        callback_data=f"extend_hold:{task_id}",
                    ),
                )

            # Row 4: task detail + operations list
            if task_id:
                builder.row(
                    tg_types.InlineKeyboardButton(
                        text="\U0001f50d تفاصيل العملية",
                        callback_data=f"task_detail:{task_id}",
                    ),
                    tg_types.InlineKeyboardButton(
                        text="\U0001f4cb العمليات",
                        callback_data="list_tasks",
                    ),
                )
            else:
                builder.row(tg_types.InlineKeyboardButton(
                    text="\U0001f4cb العمليات",
                    callback_data="list_tasks",
                ))

            await bot.send_message(
                user_id, text,
                parse_mode="HTML",
                reply_markup=builder.as_markup(),
            )
        except Exception:
            pass

    async def _fail_task(self, db, task, reason: str, ctx: Optional[ReservationSessionContext] = None):
        # ── DEAD LETTER QUEUE (DLQ) & POISON PILL PROTECTION ──
        logs = list(task.execution_logs or [])
        failure_count = sum(1 for log in logs if log.get("msg", "").startswith("CHECKOUT_FAILED") or log.get("msg", "").startswith("EXECUTION_CRASH"))
        
        if failure_count >= 3:
            # Poison pill threshold reached: do not allow retries or silent failures
            task.status = "FAILED_DLQ"
            reason = f"[POISON_PILL] {reason}"
        else:
            task.status = TaskStatus.FAILED.value
            
        task.error_message = reason
        logs.append({"ts": datetime.now(timezone.utc).isoformat(), "msg": reason, "correlation_id": ctx.correlation_id if ctx else None})
        task.execution_logs = logs
        
        # ── COMPENSATING TRANSACTION: Release orphaned holds on failure ──
        if task.hold_token:
            try:
                from modules.webook.client import WebookApiClient
                from database.models.account import AuthSession
                acc = await db.get(AuthSession, task.account_id) if task.account_id else None
                if acc and acc.bearer_token:
                    api = WebookApiClient()
                    await api.set_bearer(acc.bearer_token)
                    await api.release_reservation(slug=task.event_slug, hold_token=task.hold_token)
            except Exception as e:
                logger.error(f"[COMPENSATING_TRANSACTION_FAILED] task_id={task.id} err={e}")
                
        await db.commit()
        await self._notify_user(task.user_id, f"❌ <b>فشل الحجز</b>\n🎯 الفعالية: <code>{task.event_slug}</code>\n📌 السبب: <code>{reason[:200]}</code>", task_id=task.id)

if __name__ == "__main__":
    import os
    if os.environ.get("CHAOS_MODE") == "1":
        import sys
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        try:
            from tests.chaos_injector import inject_chaos
            inject_chaos()
        except ImportError as e:
            print(f"Failed to load Chaos Injector: {e}")


    worker = ReservationWorker()
    asyncio.run(worker.run())
