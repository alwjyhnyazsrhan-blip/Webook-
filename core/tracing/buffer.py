"""
core/tracing/buffer.py
======================
TraceBuffer â€” stores the last N traces so failures can be inspected after the fact.
Backed by an in-process ring buffer AND optionally Redis for cross-process access.

Usage
-----
    from core.tracing.buffer import trace_buffer

    # store after handler finishes
    trace_buffer.push(ctx)

    # retrieve for /debug_last_trace
    recent = trace_buffer.last(10)
    last_failure = trace_buffer.last_failure()
"""

from __future__ import annotations

import json
import asyncio
from collections import deque
from typing import Optional, List

from core.tracing.context import TraceContext, FailureSnapshot

BUFFER_SIZE  = 100   # in-process ring
REDIS_KEY    = "bot:traces:recent"
REDIS_FAIL_KEY = "bot:traces:last_failure"
REDIS_TTL    = 86400  # 24 h


class TraceBuffer:
    def __init__(self, maxlen: int = BUFFER_SIZE):
        self._ring:    deque[TraceContext]     = deque(maxlen=maxlen)
        self._failures: deque[FailureSnapshot] = deque(maxlen=20)
        self._redis    = None   # injected lazily
        self._lock     = asyncio.Lock()

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Injection â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def set_redis(self, redis_client) -> None:
        """Call once during startup with the shared async Redis client."""
        self._redis = redis_client

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Writing â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    async def push(self, ctx: TraceContext) -> None:
        async with self._lock:
            self._ring.append(ctx)
            if ctx._failure:
                self._failures.append(ctx._failure)

        if self._redis:
            await self._persist(ctx)

    async def _persist(self, ctx: TraceContext) -> None:
        try:
            payload = json.dumps(ctx.to_dict(), default=str)
            await self._redis.lpush(REDIS_KEY, payload)
            await self._redis.ltrim(REDIS_KEY, 0, BUFFER_SIZE - 1)
            await self._redis.expire(REDIS_KEY, REDIS_TTL)
            if ctx._failure:
                fail_payload = json.dumps(ctx._failure.to_dict(), default=str)
                await self._redis.set(REDIS_FAIL_KEY, fail_payload, ex=REDIS_TTL)
        except Exception:
            pass  # never let observability break the bot

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Reading â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def last(self, n: int = 10) -> List[TraceContext]:
        items = list(self._ring)
        return items[-n:]

    def last_failure(self) -> Optional[FailureSnapshot]:
        return self._failures[-1] if self._failures else None

    def last_for_user(self, user_id: int) -> Optional[TraceContext]:
        """In-memory search for the last trace from a specific user."""
        items = list(self._ring)
        for t in reversed(items):
            if t.user_id == user_id:
                return t
        return None

    def all_failures(self) -> List[FailureSnapshot]:
        return list(self._failures)

    async def last_from_redis(self, n: int = 10) -> List[dict]:
        """Fetch traces persisted to Redis (cross-process safe)."""
        if not self._redis:
            return []
        try:
            raw = await self._redis.lrange(REDIS_KEY, 0, n - 1)
            return [json.loads(r) for r in raw]
        except Exception:
            return []

    async def last_failure_from_redis(self) -> Optional[dict]:
        if not self._redis:
            return None
        try:
            raw = await self._redis.get(REDIS_FAIL_KEY)
            return json.loads(raw) if raw else None
        except Exception:
            return None

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Stats â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def stats(self) -> dict:
        items = list(self._ring)
        if not items:
            return {"total": 0, "failures": 0, "avg_ms": 0}
        return {
            "total":    len(items),
            "failures": len(self._failures),
            "avg_ms":   round(sum(t.elapsed_ms for t in items) / len(items), 1),
            "max_ms":   round(max(t.elapsed_ms for t in items), 1),
        }


# Global singleton â€” import from here everywhere
trace_buffer = TraceBuffer()

async def push_trace(ctx: TraceContext) -> None:
    await trace_buffer.push(ctx)

def new_trace(**kwargs) -> TraceContext:
    ctx = TraceContext.new(**kwargs)
    # Note: we don't push here because it's async, 
    # we push in the middleware/handlers when done.
    return ctx
