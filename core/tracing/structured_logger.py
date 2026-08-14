"""
core/tracing/structured_logger.py
==================================
Emits structured JSON log lines for every observable event.
Wraps the existing `logger` from core.logging.logger so no pipeline change needed.

Usage
-----
    from core.tracing.structured_logger import tlog

    tlog.callback_received(ctx, callback_data="sync_now")
    tlog.fsm_transition(ctx, old="None", new="choosing_category")
    tlog.keyboard_built(ctx, count=5, buttons=[...])
    tlog.telegram_edit_ok(ctx, message_id=42)
    tlog.telegram_edit_fail(ctx, exc=e)
    tlog.worker_stage(ctx, stage="TICKET_SELECTED", ticket_id="abc")
    tlog.exception(ctx, handler="handle_sync_now", exc=e)
"""

from __future__ import annotations

import json
from typing import Any, Optional, List

try:
    from core.logging.logger import logger
except ImportError:
    import logging
    logger = logging.getLogger("bot.tracing")

from core.tracing.context import TraceContext


def _emit(level: str, event: str, ctx: Optional[TraceContext], **fields) -> None:
    payload: dict = {"event": event}
    if ctx:
        payload["trace_id"]     = ctx.trace_id
        payload["user_id"]      = ctx.user_id
        payload["callback_data"] = ctx.callback_data
        payload["fsm_state"]    = ctx.fsm_state
        payload["elapsed_ms"]   = ctx.elapsed_ms
    payload.update({k: v for k, v in fields.items() if v is not None})

    # Serialize â€” keep it on one line so log parsers (Loki, Datadog, etc.) see it as one record
    line = json.dumps(payload, default=str, ensure_ascii=False)

    # Use the custom logger's info/error/etc methods which take (event: str, **kwargs)
    # We prefix with [TRACE] to distinguish from other logs
    getattr(logger, level)(f"[TRACE] {line}")


class StructuredLogger:
    """Namespace for every named log event in the bot."""

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Telegram interaction â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def callback_received(self, ctx: TraceContext, callback_data: str, **kw) -> None:
        ctx.stage("callback_received", callback_data=callback_data)
        _emit("info", "CALLBACK_RECEIVED", ctx, callback_data=callback_data, **kw)

    def handler_entered(self, ctx: TraceContext, handler: str, **kw) -> None:
        ctx.stage("handler_entered", handler=handler)
        _emit("info", "HANDLER_ENTERED", ctx, handler=handler, **kw)

    def handler_completed(self, ctx: TraceContext, handler: str, **kw) -> None:
        ctx.stage("handler_completed", handler=handler)
        _emit("info", "HANDLER_COMPLETED", ctx, handler=handler, **kw)

    def handler_failed(self, ctx: TraceContext, handler: str, exc: Exception, **kw) -> None:
        snap = ctx.snapshot(exc, handler=handler)
        _emit("error", "HANDLER_FAILED", ctx, handler=handler,
              exc_type=type(exc).__name__, exc=str(exc), **kw)
        logger.error(f"[FAILURE_SNAPSHOT]\n{snap.summary()}")

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Telegram API calls â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def telegram_edit_ok(self, ctx: TraceContext, message_id: Optional[int] = None, **kw) -> None:
        ctx.stage("telegram_edit_ok", message_id=message_id)
        _emit("info", "TELEGRAM_EDIT_OK", ctx, message_id=message_id, **kw)

    def telegram_edit_fail(self, ctx: TraceContext, exc: Exception, **kw) -> None:
        ctx.stage("telegram_edit_fail", exc=str(exc))
        _emit("warning", "TELEGRAM_EDIT_FAIL", ctx, exc=str(exc), **kw)

    def telegram_send_ok(self, ctx: TraceContext, message_id: Optional[int] = None, **kw) -> None:
        ctx.stage("telegram_send_ok", message_id=message_id)
        _emit("info", "TELEGRAM_SEND_OK", ctx, message_id=message_id, **kw)

    def telegram_send_fail(self, ctx: TraceContext, exc: Exception, **kw) -> None:
        ctx.stage("telegram_send_fail", exc=str(exc))
        _emit("error", "TELEGRAM_SEND_FAIL", ctx, exc=str(exc), **kw)

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Keyboard forensics â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def keyboard_built(
        self,
        ctx:          TraceContext,
        context_name: str,
        buttons:      List[dict],
        expected_min: int = 1,
    ) -> None:
        count      = len(buttons)
        bad_cb     = [b for b in buttons if b.get("bytes", 0) > 64]
        cb_list    = [b.get("cb", "") for b in buttons]
        ok         = count >= expected_min

        ctx.stage(
            "keyboard_built" if ok else "keyboard_too_few_buttons",
            context=context_name, count=count, expected_min=expected_min,
            bad_cb_count=len(bad_cb),
        )

        level = "info" if ok else "warning"
        _emit(level, "KEYBOARD_BUILT", ctx,
              context=context_name,
              button_count=count,
              expected_min=expected_min,
              callbacks=cb_list,
              bad_callbacks=bad_cb,
              ok=ok)

        if not ok:
            logger.warning(
                f"[KEYBOARD_FORENSIC_ALERT] context={context_name} built {count} buttons but expected>={expected_min}  "
                f"trace_id={ctx.trace_id}  THIS IS HOW THE SYNC BUG LOOKED."
            )
        if bad_cb:
            logger.error(
                f"[CALLBACK_DATA_TOO_LONG] {len(bad_cb)} button(s) exceed Telegram 64-byte limit: {bad_cb}"
            )

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ FSM â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def fsm_transition(
        self,
        ctx:       TraceContext,
        old_state: Optional[str],
        new_state: Optional[str],
        **kw,
    ) -> None:
        ctx.update_fsm(old_state, new_state)
        _emit("info", "FSM_TRANSITION", ctx, old=old_state, new=new_state, **kw)

    def fsm_cleared(self, ctx: TraceContext, **kw) -> None:
        ctx.update_fsm(ctx.fsm_state, None)
        _emit("info", "FSM_CLEARED", ctx, **kw)

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Sync / category pipeline â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def sync_start(self, ctx: TraceContext) -> None:
        ctx.stage("sync_start")
        _emit("info", "POST_SYNC_RENDER_START", ctx)

    def sync_complete(self, ctx: TraceContext, count: int) -> None:
        ctx.stage("sync_complete", event_count=count)
        _emit("info", "SYNC_COMPLETE", ctx, event_count=count)

    def categories_fetched(self, ctx: TraceContext, cats: list) -> None:
        slugs = [getattr(c, "slug", str(c)) for c in (cats or [])]
        ctx.stage("categories_fetched", count=len(slugs), slugs=slugs)
        _emit("info", "CATEGORY_FETCH_RESULT", ctx,
              count=len(slugs), categories=slugs)
        _emit("info", "CATEGORY_KEYBOARD_COUNT", ctx, count=len(slugs))
        if not slugs:
            logger.warning(
                f"[ZERO_CATEGORIES] get_live_categories() returned [] â€” "
                f"keyboard will have no category buttons.  trace_id={ctx.trace_id}"
            )

    def category_button_added(self, ctx: TraceContext, slug: str, count: int) -> None:
        ctx.stage("category_button_added", slug=slug, event_count=count)
        _emit("info", "CATEGORY_BUTTON_ADDED", ctx, slug=slug, event_count=count)

    def render_complete(self, ctx: TraceContext, **kw) -> None:
        ctx.stage("render_complete")
        _emit("info", "POST_SYNC_RENDER_COMPLETE", ctx, **kw)

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Worker pipeline â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def worker_stage(
        self,
        ctx:   Optional[TraceContext],
        stage: str,
        task_id: Optional[int] = None,
        **kw,
    ) -> None:
        if ctx:
            ctx.stage(f"worker_{stage.lower()}", task_id=task_id, **kw)
        _emit("info", f"WORKER_{stage.upper()}", ctx,
              task_id=task_id, **kw)

    def worker_ticket_selected(self, ctx: Optional[TraceContext], ticket_id: str, price: Any, **kw) -> None:
        self.worker_stage(ctx, "TICKET_SELECTED", ticket_id=ticket_id, price=price, **kw)

    def worker_ticket_none(self, ctx: Optional[TraceContext], task_id: int, slug: str, **kw) -> None:
        if ctx:
            ctx.stage("worker_ticket_none", task_id=task_id, slug=slug)
        _emit("error", "WORKER_TICKET_NOT_FOUND", ctx, task_id=task_id, slug=slug, **kw)

    def worker_checkout_start(self, ctx: Optional[TraceContext], mode: str, **kw) -> None:
        self.worker_stage(ctx, "CHECKOUT_START", mode=mode, **kw)

    def worker_checkout_fail(self, ctx: Optional[TraceContext], error: str, **kw) -> None:
        if ctx:
            ctx.stage("worker_checkout_fail", error=error)
        _emit("error", "WORKER_CHECKOUT_FAIL", ctx, error=error, **kw)

    def worker_reserved(self, ctx: Optional[TraceContext], **kw) -> None:
        self.worker_stage(ctx, "RESERVED", **kw)

    def worker_seated_fallback(
        self, ctx: Optional[TraceContext], task_id: int, reason: str, **kw
    ) -> None:
        if ctx:
            ctx.stage("worker_seated_fallback", reason=reason)
        _emit("warning", "WORKER_SEATED_FALLBACK", ctx,
              task_id=task_id, reason=reason, **kw)

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Generic â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def exception(
        self,
        ctx:     TraceContext,
        handler: str,
        exc:     Exception,
        **kw,
    ) -> None:
        self.handler_failed(ctx, handler=handler, exc=exc, **kw)


# Singleton â€” import this everywhere
tlog = StructuredLogger()
