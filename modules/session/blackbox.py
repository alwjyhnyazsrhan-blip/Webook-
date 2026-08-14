"""
Reservation Black-Box Recorder
================================
Every event in a reservation chain â€” state transitions, identity snapshots,
token acquisitions, timing checkpoints, retries â€” is captured in a structured
timeline indexed by correlation_id.

This is the forensic recorder.  When a chain fails at checkout despite a
successful hold, or is rejected despite a fresh captcha, the timeline tells you
exactly why: which identity snapshot changed, how long each stage took, which
cookie appeared or disappeared, what the proxy was, and how many retries burned.

Design
------
  - Zero external dependencies (pure stdlib + dataclasses).
  - Thread-safe for asyncio (single event loop; no concurrent writes to same
    correlation_id because account locks guarantee that).
  - Stores events in memory during the chain; call .export() at chain end to
    get the full structured dict for logging, alerting, or DB persistence.
  - Each TraceEvent has a monotonic timestamp so you can compute exact latencies
    between any two events in post-mortem analysis.

Usage
-----
    # At chain start (usually inside create_session_context):
    recorder = BlackBoxRecorder(correlation_id=ctx.correlation_id)

    # At each stage:
    recorder.record(
        event="CAPTCHA_SOLVED",
        state="CAPTCHA_VERIFIED",
        latency_ms=recorder.since_last(),
        cookie_count=len(list(ctx.httpx_client.cookies.keys())),
        proxy=ctx.proxy_id,
        retry_count=0,
        detail={"token_prefix": token[:12]},
    )

    # At chain end:
    timeline = recorder.export()
    logger.info("[BLACKBOX]", correlation_id=ctx.correlation_id, timeline=timeline)
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from core.logging.logger import logger


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Single trace event â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@dataclass
class TraceEvent:
    """One moment in the chain's lifecycle."""
    sequence:      int              # Monotonically increasing within a chain
    wall_time:     str              # ISO-8601 UTC â€” for log correlation
    mono_time:     float            # time.monotonic() â€” for latency arithmetic
    event:         str              # E.g. "CAPTCHA_SOLVED", "HOLD_ACQUIRED"
    state:         str              # SessionState at the moment of the event
    latency_ms:    Optional[float]  # ms since previous event (None for first)
    cookie_count:  int              # Number of cookies in jar at this moment
    proxy:         str              # Proxy identity hash (from ctx.proxy_id)
    fingerprint:   str              # UA fingerprint hash (from ctx.ua_hash)
    retry_count:   int              # Cumulative retries at this point
    detail:        Dict[str, Any]   # Event-specific payload (token prefix, etc.)

    def to_dict(self) -> dict:
        return {
            "seq":          self.sequence,
            "time":         self.wall_time,
            "event":        self.event,
            "state":        self.state,
            "latency_ms":   round(self.latency_ms, 2) if self.latency_ms is not None else None,
            "cookie_count": self.cookie_count,
            "proxy":        self.proxy,
            "fingerprint":  self.fingerprint,
            "retry_count":  self.retry_count,
            **self.detail,
        }


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Recorder â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

class BlackBoxRecorder:
    """
    Append-only timeline for one reservation chain.

    One instance per correlation_id.  Created at chain start, exported at end.
    """

    def __init__(
        self,
        correlation_id: str,
        account_id: str,
        event_slug: str,
        flow_type: str,
        proxy: str,
        fingerprint: str,
    ):
        self.correlation_id = correlation_id
        self.account_id     = account_id
        self.event_slug     = event_slug
        self.flow_type      = flow_type

        self._events: List[TraceEvent] = []
        self._start_mono  = time.monotonic()
        self._last_mono   = self._start_mono
        self._start_wall  = datetime.now(timezone.utc).isoformat()
        self._proxy       = proxy
        self._fingerprint = fingerprint

        # Record the chain-open event immediately
        self.record(
            event="CHAIN_OPENED",
            state="INITIALIZED",
            cookie_count=0,
            retry_count=0,
            detail={
                "account_id": account_id,
                "event_slug": event_slug,
                "flow_type":  flow_type,
            },
        )

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Core append â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def record(
        self,
        event: str,
        state: str,
        cookie_count: int = 0,
        retry_count: int  = 0,
        detail: Optional[Dict[str, Any]] = None,
        proxy: Optional[str] = None,
        fingerprint: Optional[str] = None,
    ) -> TraceEvent:
        """
        Append one event to the timeline.

        Parameters
        ----------
        event       : Short event name, e.g. "HOLD_ACQUIRED".
        state       : Current SessionState value string.
        cookie_count: len(list(ctx.httpx_client.cookies.keys()))
        retry_count : Cumulative retries at this moment.
        detail      : Arbitrary event-specific payload.
        proxy       : Override the chain-level proxy hash (e.g. if proxy rotated).
        fingerprint : Override the chain-level fingerprint hash.
        """
        now_mono = time.monotonic()
        latency  = (now_mono - self._last_mono) * 1000 if self._events else None  # ms
        self._last_mono = now_mono

        ev = TraceEvent(
            sequence     = len(self._events),
            wall_time    = datetime.now(timezone.utc).isoformat(),
            mono_time    = now_mono,
            event        = event,
            state        = state,
            latency_ms   = latency,
            cookie_count = cookie_count,
            proxy        = proxy or self._proxy,
            fingerprint  = fingerprint or self._fingerprint,
            retry_count  = retry_count,
            detail       = detail or {},
        )
        self._events.append(ev)
        return ev

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Convenience helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def since_last(self) -> float:
        """Milliseconds since the previous recorded event."""
        return (time.monotonic() - self._last_mono) * 1000

    def total_elapsed_ms(self) -> float:
        """Total milliseconds since chain opened."""
        return (time.monotonic() - self._start_mono) * 1000

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Export â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def export(self, outcome: str = "UNKNOWN") -> dict:
        """
        Return the full structured timeline.

        Parameters
        ----------
        outcome : Final chain outcome â€” "SUCCESS", "FAILED", "ABORTED", etc.
        """
        total_ms = self.total_elapsed_ms()
        events   = [e.to_dict() for e in self._events]

        timeline = {
            "correlation_id":  self.correlation_id,
            "account_id":      self.account_id,
            "event_slug":      self.event_slug,
            "flow_type":       self.flow_type,
            "started_at":      self._start_wall,
            "total_ms":        round(total_ms, 2),
            "outcome":         outcome,
            "event_count":     len(events),
            "events":          events,
        }

        logger.info(
            f"[BLACKBOX_EXPORT] correlation_id={self.correlation_id} "
            f"outcome={outcome} total_ms={total_ms:.0f} events={len(events)}"
        )
        return timeline

    def log_summary(self) -> None:
        """
        Emit a compact summary log â€” useful at chain end without full export.
        """
        total_ms = self.total_elapsed_ms()
        stages   = [e.event for e in self._events]
        logger.info(
            f"[BLACKBOX_SUMMARY] correlation_id={self.correlation_id} "
            f"total_ms={total_ms:.0f} "
            f"events={len(self._events)} "
            f"stages={stages}"
        )

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Convenience: render ASCII timeline â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def render_ascii(self) -> str:
        """
        Return a human-readable ASCII timeline for console debugging.

        Example output:
            â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ CHAIN_OPENED           t=0 ms      cookies=0  proxy=abc123
            â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ CAPTCHA_PENDING        t=120 ms     Î”120ms     cookies=3
            â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ CAPTCHA_SOLVED         t=14320 ms   Î”14200ms   cookies=3
            â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ HOLD_ACQUIRED          t=15890 ms   Î”1570ms    cookies=5
            â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ CHECKOUT_SENT          t=24100 ms   Î”8210ms    cookies=5
            â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ PAYMENT_SESSION_CREATED t=25800 ms  Î”1700ms    cookies=7
            â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ CHAIN_CLOSED           t=25810 ms   Î”10ms
        """
        lines = []
        start = self._events[0].mono_time if self._events else self._start_mono
        for i, ev in enumerate(self._events):
            connector = "â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€" if i == len(self._events) - 1 else "â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€"
            abs_ms    = (ev.mono_time - start) * 1000
            delta     = f"  Î”{ev.latency_ms:.0f}ms" if ev.latency_ms is not None else ""
            lines.append(
                f"{connector} {ev.event:<28} t={abs_ms:>8.0f}ms{delta:<12} "
                f"cookies={ev.cookie_count}  proxy={ev.proxy[:8]}"
            )
        header = (
            f"â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ BLACKBOX: {self.correlation_id}\n"
            f"â”‚   account={self.account_id}  slug={self.event_slug}  flow={self.flow_type}\n"
            f"â”‚"
        )
        return header + "\n".join(lines)
