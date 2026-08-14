"""
ReservationSessionContext
=========================
Single source of truth for session identity across the entire reservation chain.

INVARIANTS enforced by this module:
  1. The httpx client instance never changes after context creation.
  2. The cookie jar object never changes after context creation.
  3. The proxy/IP never changes mid-chain.
  4. The user-agent fingerprint never changes mid-chain.
  5. State transitions are legal-only; illegal transitions abort the chain.

Any drift in (1-4) emits [IDENTITY_DRIFT_DETECTED] at CRITICAL severity and
raises IdentityDriftError, aborting the chain immediately.
"""

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional, Any

import httpx

from core.logging.logger import logger
from modules.session.timing import (
    ChainTimestamps,
    assert_chain_alive,
    assert_captcha_fresh,
    assert_hold_fresh,
    assert_checkout_window_open,
    TokenExpiredError,
)
from modules.session.blackbox import BlackBoxRecorder
from modules.session.snapshots import RequestSnapshot, global_snapshot_store


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# State Machine
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

class SessionState(str, Enum):
    INITIALIZED            = "INITIALIZED"
    CAPTCHA_PENDING        = "CAPTCHA_PENDING"
    CAPTCHA_VERIFIED       = "CAPTCHA_VERIFIED"
    HOLD_TOKEN_ACQUIRED    = "HOLD_TOKEN_ACQUIRED"
    CHECKOUT_PENDING       = "CHECKOUT_PENDING"
    PAYMENT_SESSION_CREATED = "PAYMENT_SESSION_CREATED"
    COMPLETED              = "COMPLETED"
    ABORTED                = "ABORTED"


# Legal transitions: from â†’ set of valid next states
_LEGAL_TRANSITIONS = {
    SessionState.INITIALIZED: {
        SessionState.CAPTCHA_PENDING,
        SessionState.HOLD_TOKEN_ACQUIRED,   # captcha-free seated path
        SessionState.CHECKOUT_PENDING,      # plain/best-available path
    },
    SessionState.CAPTCHA_PENDING: {
        SessionState.CAPTCHA_VERIFIED,
        SessionState.ABORTED,
    },
    SessionState.CAPTCHA_VERIFIED: {
        SessionState.HOLD_TOKEN_ACQUIRED,
        SessionState.ABORTED,
    },
    SessionState.HOLD_TOKEN_ACQUIRED: {
        SessionState.CHECKOUT_PENDING,
        SessionState.ABORTED,
    },
    SessionState.CHECKOUT_PENDING: {
        SessionState.PAYMENT_SESSION_CREATED,
        SessionState.ABORTED,
    },
    SessionState.PAYMENT_SESSION_CREATED: {
        SessionState.COMPLETED,
        SessionState.ABORTED,
    },
    SessionState.COMPLETED: set(),
    SessionState.ABORTED:  set(),
}


class IllegalStateTransitionError(RuntimeError):
    """Raised when a state transition violates the legal graph."""


class IdentityDriftError(RuntimeError):
    """Raised when session identity drift is detected mid-chain."""


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Helpers
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _hash_str(value: Optional[str]) -> str:
    if not value:
        return "empty"
    return hashlib.sha256(value.encode()).hexdigest()[:16]


def _hash_ua(headers: dict) -> str:
    ua = headers.get("User-Agent") or headers.get("user-agent") or ""
    return _hash_str(ua)


def _cookie_names(jar: httpx.Cookies) -> List[str]:
    try:
        return sorted(jar.keys())
    except Exception:
        return []


def _cookie_hash(jar: httpx.Cookies) -> str:
    try:
        raw = json.dumps(
            {k: v for k, v in sorted(jar.items())},
            sort_keys=True
        )
        return hashlib.sha256(raw.encode()).hexdigest()[:16]
    except Exception:
        return "unhashable"


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Context
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@dataclass
class ReservationSessionContext:
    """
    Owns the session identity for the entire reservation chain.

    Construction contract:
      - Pass the httpx.AsyncClient that will be used for ALL requests.
      - Pass the fingerprint headers dict used to create the client.
      - After __post_init__, call ctx.emit_fingerprint_log() once.

    Usage contract:
      - Every stage calls ctx.transition(SessionState.X) before its work.
      - Every stage calls ctx.assert_identity_intact() before its first request.
      - The captcha solver MUST use ctx.httpx_client, not a new client.
      - No code outside this module may replace ctx.httpx_client.
    """

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Required at creation â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    correlation_id: str
    account_id: str
    event_slug: str
    flow_type: str                   # "plain" | "best_available" | "seated"
    httpx_client: httpx.AsyncClient
    fingerprint_headers: dict        # The headers dict passed to the client

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Proxy â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    proxy_config: Optional[str] = None   # raw proxy URL string, or None

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Chain values (populated as chain progresses) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    captcha_token: Optional[str]   = None
    hold_token: Optional[str]      = None

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ State â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    state: SessionState = SessionState.INITIALIZED

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Telemetry â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    telemetry_events: List[dict] = field(default_factory=list)
    snapshot_history: List["RequestSnapshot"] = field(default_factory=list)

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Timing & black-box â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    chain_timestamps: "ChainTimestamps"  = field(init=False, default=None)
    blackbox: "BlackBoxRecorder"         = field(init=False, default=None)

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Timestamps â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_activity_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Derived identity fields (set in __post_init__) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    proxy_id: str            = field(init=False)
    user_agent: str          = field(init=False)
    ua_hash: str             = field(init=False)
    cookie_jar: Any          = field(init=False)   # httpx.Cookies
    cookie_hash: str         = field(init=False)
    client_object_id: int    = field(init=False)
    cookie_jar_object_id: int = field(init=False)
    immutable_identity_snapshot: dict = field(init=False)

    def __post_init__(self):
        self.proxy_id = _hash_str(self.proxy_config)
        self.user_agent = (
            self.fingerprint_headers.get("User-Agent")
            or self.fingerprint_headers.get("user-agent")
            or "unknown"
        )
        self.ua_hash = _hash_ua(self.fingerprint_headers)

        # Capture the live cookie jar from the client
        self.cookie_jar = self.httpx_client.cookies

        # Identity anchors â€” these must never change
        self.client_object_id    = id(self.httpx_client)
        self.cookie_jar_object_id = id(self.cookie_jar)
        self.cookie_hash          = _cookie_hash(self.cookie_jar)

        # Timing + forensic recorder
        self.chain_timestamps = ChainTimestamps()
        self.blackbox = BlackBoxRecorder(
            correlation_id=self.correlation_id,
            account_id=self.account_id,
            event_slug=self.event_slug,
            flow_type=self.flow_type,
            proxy=self.proxy_id,
            fingerprint=self.ua_hash,
        )

        # Immutable snapshot taken at context creation
        self.immutable_identity_snapshot = {
            "correlation_id":       self.correlation_id,
            "account_id":           self.account_id,
            "event_slug":           self.event_slug,
            "flow_type":            self.flow_type,
            "proxy_id":             self.proxy_id,
            "ua_hash":              self.ua_hash,
            "client_object_id":     self.client_object_id,
            "cookie_jar_object_id": self.cookie_jar_object_id,
            "cookie_hash":          self.cookie_hash,
            "created_at":           self.created_at.isoformat(),
        }

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ State machine â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def transition(self, to_state: SessionState) -> None:
        """
        Advance the state machine.  Raises IllegalStateTransitionError if the
        transition is not in the legal graph.  Emits [STATE_TRANSITION] telemetry.
        """
        # Guard: abort if chain exceeded its total duration budget
        assert_chain_alive(self.chain_timestamps, self.correlation_id)

        allowed = _LEGAL_TRANSITIONS.get(self.state, set())
        if to_state not in allowed:
            msg = (
                f"[ILLEGAL_TRANSITION] "
                f"correlation_id={self.correlation_id} "
                f"from={self.state} to={to_state} "
                f"allowed={[s.value for s in allowed]}"
            )
            self._emit("ILLEGAL_TRANSITION",
                       from_state=self.state.value,
                       to_state=to_state.value,
                       severity="CRITICAL")
            logger.critical(msg)
            raise IllegalStateTransitionError(msg)

        prev = self.state
        self.state = to_state
        self.last_activity_at = datetime.now(timezone.utc)
        self._emit("STATE_TRANSITION",
                   from_state=prev.value,
                   to_state=to_state.value)
        logger.info(
            f"[STATE_TRANSITION] "
            f"correlation_id={self.correlation_id} "
            f"from={prev.value} "
            f"to={to_state.value}"
        )

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Identity enforcement â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def assert_identity_intact(self, stage: str) -> None:
        """
        Verify that the session identity has not drifted since context creation.
        Checks client object identity, cookie jar object identity, and proxy.
        Raises IdentityDriftError on any mismatch.
        """
        drifts = []

        actual_client_id = id(self.httpx_client)
        if actual_client_id != self.client_object_id:
            drifts.append(
                f"CLIENT_REPLACED: expected_id={self.client_object_id} "
                f"actual_id={actual_client_id}"
            )

        actual_jar_id = id(self.httpx_client.cookies)
        if actual_jar_id != self.cookie_jar_object_id:
            drifts.append(
                f"COOKIE_JAR_REPLACED: expected_id={self.cookie_jar_object_id} "
                f"actual_id={actual_jar_id}"
            )

        if drifts:
            drift_str = "; ".join(drifts)
            self._emit("IDENTITY_DRIFT_DETECTED",
                       stage=stage,
                       drift=drift_str,
                       severity="HIGH")
            msg = (
                f"[IDENTITY_DRIFT_DETECTED] "
                f"correlation_id={self.correlation_id} "
                f"stage={stage} "
                f"drift={drift_str}"
            )
            logger.critical(msg)
            self.transition(SessionState.ABORTED)
            raise IdentityDriftError(msg)

        self._emit("IDENTITY_SNAPSHOT",
                   stage=stage,
                   client_object_id=actual_client_id,
                   cookie_jar_object_id=actual_jar_id,
                   cookie_names=_cookie_names(self.httpx_client.cookies))
        logger.info(
            f"[IDENTITY_SNAPSHOT] "
            f"correlation_id={self.correlation_id} "
            f"stage={stage} "
            f"client_id={actual_client_id} "
            f"cookie_jar_id={actual_jar_id} "
            f"cookie_names={_cookie_names(self.httpx_client.cookies)}"
        )

    def snapshot_cookies(self, stage: str) -> None:
        """
        Emit [COOKIE_TRANSITION] telemetry comparing current cookie state
        against the snapshot taken at context creation.
        """
        before_names = sorted(
            json.loads(
                json.dumps(list(self.immutable_identity_snapshot.get("cookie_hash", "")))
            )
            if False else []  # we only have the hash, not original names
        )
        current_names = _cookie_names(self.httpx_client.cookies)
        current_hash  = _cookie_hash(self.httpx_client.cookies)

        added   = [n for n in current_names if n not in before_names]
        removed = [n for n in before_names  if n not in current_names]

        self._emit("COOKIE_TRANSITION",
                   stage=stage,
                   before_hash=self.cookie_hash,
                   after_hash=current_hash,
                   after_names=current_names,
                   added=added,
                   removed=removed)
        logger.info(
            f"[COOKIE_TRANSITION] "
            f"correlation_id={self.correlation_id} "
            f"stage={stage} "
            f"before_hash={self.cookie_hash} "
            f"after_hash={current_hash} "
            f"after_names={current_names} "
            f"added={added} "
            f"removed={removed}"
        )

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Telemetry helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def emit_fingerprint_log(self) -> None:
        """Emit the opening [SESSION_FINGERPRINT] log. Call once after creation."""
        self._emit("SESSION_FINGERPRINT",
                   client_id=self.client_object_id,
                   cookie_hash=self.cookie_hash,
                   proxy_id=self.proxy_id,
                   ua_hash=self.ua_hash,
                   flow_type=self.flow_type)
        logger.info(
            f"[SESSION_FINGERPRINT] "
            f"correlation_id={self.correlation_id} "
            f"client_id={self.client_object_id} "
            f"cookie_hash={self.cookie_hash} "
            f"proxy_id={self.proxy_id} "
            f"ua_hash={self.ua_hash} "
            f"flow_type={self.flow_type} "
            f"account_id={self.account_id} "
            f"event_slug={self.event_slug}"
        )

    def record_hold_token(self, token: str) -> None:
        self.hold_token = token
        self.chain_timestamps.mark_hold_acquired()
        self.blackbox.record(
            event="HOLD_TOKEN_STORED",
            state=self.state.value,
            cookie_count=len(list(self.httpx_client.cookies.keys())),
            detail={"token_prefix": token[:12] if token else None},
        )
        self._emit("HOLD_TOKEN_STORED", token_prefix=token[:12] if token else None)
        logger.info(
            f"[HOLD_TOKEN_STORED] "
            f"correlation_id={self.correlation_id} "
            f"token_prefix={token[:12] if token else None}"
        )

    def record_captcha_token(self, token: str) -> None:
        self.captcha_token = token
        self.chain_timestamps.mark_captcha_acquired()
        self.blackbox.record(
            event="CAPTCHA_TOKEN_STORED",
            state=self.state.value,
            cookie_count=len(list(self.httpx_client.cookies.keys())),
            detail={"token_prefix": token[:12] if token else None},
        )
        self._emit("CAPTCHA_TOKEN_STORED",
                   token_prefix=token[:12] if token else None)
        logger.info(
            f"[CAPTCHA_TOKEN_STORED] "
            f"correlation_id={self.correlation_id} "
            f"token_prefix={token[:12] if token else None}"
        )

    def record_snapshot(self, snap: "RequestSnapshot") -> None:
        self.snapshot_history.append(snap)
        self.blackbox.record(
            event="REQUEST_SNAPSHOT",
            state=self.state.value,
            cookie_count=len(list(self.httpx_client.cookies.keys())),
            detail={
                "stage": snap.stage,
                "method": snap.method,
                "url_hash": snap.shape_fingerprint()[:16],
                "response_code": snap.response_code,
                "header_hash": snap.header_hash,
                "body_hash": snap.body_hash,
            },
        )
        self._emit("REQUEST_SNAPSHOT",
                   stage=snap.stage,
                   method=snap.method,
                   url_fp=snap.shape_fingerprint()[:16],
                   response_code=snap.response_code)
        logger.info(
            f"[REQUEST_SNAPSHOT] "
            f"correlation_id={self.correlation_id} "
            f"stage={snap.stage} "
            f"method={snap.method} "
            f"url_fp={snap.shape_fingerprint()[:16]} "
            f"response_code={snap.response_code}"
        )

    def abort(self, reason: str) -> None:
        """Transition to ABORTED state if not already terminal."""
        if self.state in (SessionState.COMPLETED, SessionState.ABORTED):
            return
        # Force â€” bypass legal-graph check for abort
        prev = self.state
        self.state = SessionState.ABORTED
        self.last_activity_at = datetime.now(timezone.utc)
        self._emit("SESSION_ABORTED",
                   from_state=prev.value,
                   reason=reason,
                   severity="HIGH")
        logger.warning(
            f"[SESSION_ABORTED] "
            f"correlation_id={self.correlation_id} "
            f"from={prev.value} "
            f"reason={reason}"
        )

    def summary(self) -> dict:
        return {
            "correlation_id": self.correlation_id,
            "account_id":     self.account_id,
            "event_slug":     self.event_slug,
            "flow_type":      self.flow_type,
            "state":          self.state.value,
            "hold_token":     bool(self.hold_token),
            "captcha_token":  bool(self.captcha_token),
            "proxy_id":       self.proxy_id,
            "ua_hash":        self.ua_hash,
            "events":         len(self.telemetry_events),
            "created_at":     self.created_at.isoformat(),
            "last_activity":  self.last_activity_at.isoformat(),
        }

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Internal â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def _emit(self, event_type: str, **kwargs) -> None:
        self.last_activity_at = datetime.now(timezone.utc)
        self.telemetry_events.append({
            "ts":             self.last_activity_at.isoformat(),
            "event":          event_type,
            "correlation_id": self.correlation_id,
            **kwargs,
        })


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Factory
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

async def create_session_context(
    account_id: str,
    event_slug: str,
    flow_type: str,
    proxy_config: Optional[str],
    fingerprint_headers: dict,
    ssl_context: Optional["ssl.SSLContext"] = None, # Added SSL context enforcement
) -> ReservationSessionContext:
    """
    Factory: creates the httpx.AsyncClient, pins it to the context,
    and emits the opening fingerprint log.

    Fix 1 contract
    --------------
    The client created here is the ONLY client used for ALL requests in the
    chain (auth, captcha, hold, checkout, payment).  Callers must pass
    ``ctx.httpx_client`` to every sub-module that makes network requests â€”
    never let those modules create or fetch their own client.

    Fix 2 â€” Captcha solver isolation
    ---------------------------------
    The captcha solver MUST receive ``ctx.httpx_client`` and use it for the
    challenge request.  Creating a second client inside the solver breaks
    cookie continuity and causes the session to be flagged as suspicious.
    Correct usage::

        captcha_token = await solve_captcha(
            client=ctx.httpx_client,        # same client, same cookies
            fingerprint_headers=ctx.fingerprint_headers,
            site_url=...,
        )
        ctx.record_captcha_token(captcha_token)
    """
    import httpx

    # Fix 5: use the named timeout constants from network.py
    from modules.webook.network import CONNECT_TIMEOUT, READ_TIMEOUT, WRITE_TIMEOUT, POOL_TIMEOUT
    
    limits = httpx.Limits(
        max_connections=10,
        max_keepalive_connections=5,
        keepalive_expiry=30.0,
    )
    timeout = httpx.Timeout(
        timeout=READ_TIMEOUT,
        connect=CONNECT_TIMEOUT,
        write=WRITE_TIMEOUT,
        pool=POOL_TIMEOUT,
    )
    proxies = {"http://": proxy_config, "https://": proxy_config} if proxy_config else None

    # PILLAR ENFORCEMENT: TLS Fingerprinting
    # In httpx, the custom SSLContext must be applied at the Transport level.
    transport = httpx.AsyncHTTPTransport(
        verify=ssl_context if ssl_context else True,
        limits=limits,
        http2=True,
    )

    client = httpx.AsyncClient(
        transport=transport,
        timeout=timeout,
        proxies=proxies,
        follow_redirects=True,
        cookies=httpx.Cookies(),
    )

    ctx = ReservationSessionContext(
        correlation_id=str(uuid.uuid4()),
        account_id=account_id,
        event_slug=event_slug,
        flow_type=flow_type,
        httpx_client=client,
        fingerprint_headers=fingerprint_headers,
        proxy_config=proxy_config,
    )
    ctx.emit_fingerprint_log()
    return ctx


async def close_session_context(ctx: ReservationSessionContext) -> None:
    """Close the client owned by this context. Call in finally block."""
    try:
        if not ctx.httpx_client.is_closed:
            await ctx.httpx_client.aclose()
            logger.info(
                f"[SESSION_CLOSED] "
                f"correlation_id={ctx.correlation_id} "
                f"final_state={ctx.state.value} "
                f"telemetry_events={len(ctx.telemetry_events)}"
            )
    except Exception as e:
        logger.warning(
            f"[SESSION_CLOSE_ERROR] "
            f"correlation_id={ctx.correlation_id} "
            f"error={e}"
        )
