"""
core/tracing/context.py
=======================
TraceContext â€” one object created per user interaction, passed through every
handler, service, and worker stage.  Carries the full correlation chain.

Usage
-----
    ctx = TraceContext.new(user_id=123, chat_id=456, callback_data="sync_now")
    ctx.stage("sync_start")
    ctx.stage("categories_fetched", count=5)
    ctx.keyboard_check(builder, expected_min=1)
    # on exception:
    ctx.snapshot(exc, handler="handle_sync_now", fsm_state="choosing_category")
"""

from __future__ import annotations

import time
import uuid
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Stage record â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@dataclass
class Stage:
    name:      str
    ts:        float = field(default_factory=time.monotonic)
    wall:      str   = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    extra:     Dict  = field(default_factory=dict)

    def elapsed_ms(self, since: float) -> float:
        return round((self.ts - since) * 1000, 1)

    def to_dict(self) -> dict:
        return {"stage": self.name, "wall": self.wall, **self.extra}


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Failure snapshot â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@dataclass
class FailureSnapshot:
    trace_id:     str
    user_id:      Optional[int]
    handler:      str
    exception:    str
    exc_type:     str
    traceback_str: str
    fsm_state:    Optional[str]
    callback_data: Optional[str]
    keyboard_info: Optional[dict]
    stage_chain:  List[str]
    wall:         str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "trace_id":     self.trace_id,
            "user_id":      self.user_id,
            "handler":      self.handler,
            "exception":    self.exception,
            "exc_type":     self.exc_type,
            "traceback":    self.traceback_str,
            "fsm_state":    self.fsm_state,
            "callback_data": self.callback_data,
            "keyboard_info": self.keyboard_info,
            "stage_chain":  self.stage_chain,
            "wall":         self.wall,
        }

    def summary(self) -> str:
        chain = " â†’ ".join(self.stage_chain[-8:])  # last 8 stages
        return (
            f"[FAILURE_SNAPSHOT]\n"
            f"  trace_id     = {self.trace_id}\n"
            f"  user_id      = {self.user_id}\n"
            f"  handler      = {self.handler}\n"
            f"  exception    = {self.exc_type}: {self.exception}\n"
            f"  fsm_state    = {self.fsm_state}\n"
            f"  callback     = {self.callback_data}\n"
            f"  keyboard     = {self.keyboard_info}\n"
            f"  stage_chain  = {chain}\n"
            f"  wall         = {self.wall}"
        )


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ TraceContext â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

class TraceContext:
    """
    One instance per Telegram update.  Thread-safe for concurrent async tasks
    because each update gets its own object; never shared across updates.
    """

    def __init__(
        self,
        *,
        user_id:       Optional[int]  = None,
        chat_id:       Optional[int]  = None,
        message_id:    Optional[int]  = None,
        callback_data: Optional[str]  = None,
        fsm_state:     Optional[str]  = None,
        trace_id:      Optional[str]  = None,
        parent_trace_id: Optional[str] = None,
        root_trace_id: Optional[str] = None,
        depth: int = 0
    ):
        self.trace_id:     str            = trace_id or uuid.uuid4().hex[:12]
        self.parent_trace_id: Optional[str] = parent_trace_id
        self.root_trace_id: str = root_trace_id or self.trace_id
        self.depth: int = depth
        self.user_id:      Optional[int]  = user_id
        self.chat_id:      Optional[int]  = chat_id
        self.message_id:   Optional[int]  = message_id
        self.callback_data: Optional[str] = callback_data
        self.fsm_state:    Optional[str]  = fsm_state
        self.started_at:   float          = time.monotonic()
        self.wall_start:   str            = datetime.now(timezone.utc).isoformat()
        self._stages:      List[Stage]    = []
        self._failure:     Optional[FailureSnapshot] = None

        # keyboard telemetry for the current render pass
        self._last_keyboard_info: Optional[dict] = None

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Factory â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    @property
    def stages(self) -> List[Stage]:
        return self._stages

    @classmethod
    def new(
        cls,
        user_id:       Optional[int] = None,
        chat_id:       Optional[int] = None,
        message_id:    Optional[int] = None,
        callback_data: Optional[str] = None,
        fsm_state:     Optional[str] = None,
        trace_id:      Optional[str] = None,
        parent_trace_id: Optional[str] = None,
        root_trace_id: Optional[str] = None,
        depth: int = 0,
        **kwargs
    ) -> "TraceContext":
        return cls(
            user_id=user_id,
            chat_id=chat_id,
            message_id=message_id,
            callback_data=callback_data,
            fsm_state=fsm_state,
            trace_id=trace_id,
            parent_trace_id=parent_trace_id,
            root_trace_id=root_trace_id,
            depth=depth
        )

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Stage recording â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def stage(self, name: str, **extra) -> "TraceContext":
        """Record a named stage.  Returns self for chaining."""
        s = Stage(name=name, extra={k: v for k, v in extra.items() if v is not None})
        self._stages.append(s)
        return self

    def update_fsm(self, old_state: Optional[str], new_state: Optional[str]) -> "TraceContext":
        self.fsm_state = new_state
        return self.stage("fsm_transition", old=old_state, new=new_state)

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Keyboard forensics â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def keyboard_check(
        self,
        markup,           # InlineKeyboardMarkup or InlineKeyboardBuilder
        context_name: str = "unknown",
        expected_min: int = 1,
    ) -> "TraceContext":
        """
        Inspect a keyboard before sending.  Logs button count + every
        callback_data.  FAILS LOUDLY if count < expected_min.
        """
        from aiogram.utils.keyboard import InlineKeyboardBuilder

        if isinstance(markup, InlineKeyboardBuilder):
            built = markup.as_markup()
        else:
            built = markup

        buttons     = []
        bad_lengths = []

        if built and hasattr(built, "inline_keyboard"):
            for row in built.inline_keyboard:
                for btn in row:
                    cb   = getattr(btn, "callback_data", None) or ""
                    text = getattr(btn, "text", "")
                    cb_bytes = len(cb.encode())
                    buttons.append({"text": text, "cb": cb, "bytes": cb_bytes})
                    if cb_bytes > 64:
                        bad_lengths.append({"cb": cb, "bytes": cb_bytes})

        info = {
            "context":      context_name,
            "button_count": len(buttons),
            "buttons":      buttons,
            "bad_cb_data":  bad_lengths,
        }
        self._last_keyboard_info = info

        severity = "keyboard_ok" if len(buttons) >= expected_min else "keyboard_too_few_buttons"
        self.stage(severity, **info)

        return self

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Failure snapshot â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def snapshot(
        self,
        exc:      Exception,
        handler:  str = "unknown",
        **extra,
    ) -> FailureSnapshot:
        tb  = traceback.format_exc()
        snap = FailureSnapshot(
            trace_id      = self.trace_id,
            user_id       = self.user_id,
            handler       = handler,
            exception     = str(exc),
            exc_type      = type(exc).__name__,
            traceback_str = tb,
            fsm_state     = self.fsm_state,
            callback_data = self.callback_data,
            keyboard_info = self._last_keyboard_info,
            stage_chain   = [s.name for s in self._stages],
        )
        self._failure = snap
        self.stage("exception_captured", exc_type=type(exc).__name__, handler=handler)
        return snap

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Serialisation â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    @property
    def elapsed_ms(self) -> float:
        return round((time.monotonic() - self.started_at) * 1000, 1)

    def to_dict(self) -> dict:
        return {
            "trace_id":     self.trace_id,
            "parent_trace_id": self.parent_trace_id,
            "root_trace_id":   self.root_trace_id,
            "depth":           self.depth,
            "user_id":      self.user_id,
            "chat_id":      self.chat_id,
            "callback_data": self.callback_data,
            "fsm_state":    self.fsm_state,
            "elapsed_ms":   self.elapsed_ms,
            "wall_start":   self.wall_start,
            "stages":       [s.to_dict() for s in self._stages],
            "failure":      self._failure.to_dict() if self._failure else None,
        }

    def chain_str(self) -> str:
        """Human-readable stage chain for logs."""
        parts = [f"[{self.trace_id}]"]
        start = self.started_at
        for s in self._stages:
            ms = s.elapsed_ms(start)
            extra_str = ""
            if s.extra:
                extra_str = " " + " ".join(
                    f"{k}={v}" for k, v in list(s.extra.items())[:4]
                )
            parts.append(f"  +{ms:6.0f}ms â†’ {s.name}{extra_str}")
        if self._failure:
            parts.append(f"  !! FAILED: {self._failure.exc_type}: {self._failure.exception}")
        return "\n".join(parts)
