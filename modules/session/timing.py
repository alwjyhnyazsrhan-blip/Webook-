"""
Session Timing & Freshness Enforcement
=======================================
Anti-bot systems correlate timing realism as aggressively as they correlate
TLS fingerprints.  A captcha token submitted 4 minutes after acquisition, or a
checkout request sent 2 seconds after a hold, looks nothing like a human.

This module is the single source of truth for all timing budgets in the
reservation chain.  Every stage that has a maximum allowed age or delay imports
its constant from here.

Architecture
------------
                       â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                       â”‚  CHAIN TIMELINE (absolute budgets)  â”‚
                       â”‚                                     â”‚
  INIT â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–º â”‚  captcha acquired                   â”‚
                       â”‚  â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ MAX_CAPTCHA_AGE = 90s          â”‚
                       â”‚  â”‚   (from token issue to use)      â”‚
                       â”‚  â”‚                                  â”‚
                       â”‚  hold acquired                      â”‚
                       â”‚  â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ MAX_HOLD_TOKEN_AGE = 45s       â”‚
                       â”‚  â”‚   (hold window before expiry)    â”‚
                       â”‚  â”‚                                  â”‚
                       â”‚  checkout sent                      â”‚
                       â”‚  â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ MAX_CHECKOUT_DELAY = 30s       â”‚
                       â”‚  â”‚   (from hold to checkout POST)   â”‚
                       â”‚  â”‚                                  â”‚
                       â”‚  MAX_TOTAL_CHAIN_DURATION = 300s    â”‚
                       â”‚      (hard wall for entire chain)   â”‚
                       â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜

Timing realism bands (human behaviour research):
  - Captcha solve:   12â€“35 s   (humans are slow; < 5 s is bot-like)
  - Post-captcha:    1.5â€“4 s   (brief "I'm human" pause)
  - Seat selection:  3â€“12 s    (scanning the map)
  - Checkout:        8â€“20 s    (reading the order summary)
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from core.logging.logger import logger


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Hard budget constants (seconds) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

# Captcha tokens have a server-side TTL.  Webook's is ~120 s, but we abort at
# 90 s to leave headroom for network round-trips.
MAX_CAPTCHA_AGE: float = 90.0

# Hold tokens start expiring immediately.  Webook's observed hold window is
# 60â€“90 s; we treat 45 s as the safe upper bound to leave checkout headroom.
MAX_HOLD_TOKEN_AGE: float = 45.0

# Maximum time between hold acquisition and checkout POST.  Exceeding this
# correlates with abandoned-cart patterns that trigger re-verification.
MAX_CHECKOUT_DELAY: float = 30.0

# Absolute wall-clock budget for the entire reservation chain.
# Any chain that has been alive longer than this is almost certainly stale
# or stuck; abort and let the worker retry from scratch.
MAX_TOTAL_CHAIN_DURATION: float = 300.0

# Minimum realistic human delays (seconds) â€” used by simulators, not enforced
# by this module, but documented here as the canonical reference.
MIN_CAPTCHA_SOLVE_TIME: float = 12.0
MIN_POST_CAPTCHA_PAUSE: float = 1.5
MIN_SEAT_SELECTION_TIME: float = 3.0
MIN_CHECKOUT_REVIEW_TIME: float = 8.0


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Exception â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

class TokenExpiredError(RuntimeError):
    """
    Raised when a timing assertion fails â€” i.e. a token or stage deadline
    has been exceeded.  Callers should catch this, log it, and abort the
    ReservationSessionContext.
    """


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Timestamp record â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@dataclass
class ChainTimestamps:
    """
    Immutable (write-once) timestamp log for one reservation chain.

    Each field is set once by the corresponding stage; subsequent writes
    raise AssertionError so no stage can accidentally overwrite a sibling's
    timing data.
    """
    chain_started_at: float = field(default_factory=time.monotonic)

    _captcha_acquired_at: Optional[float] = field(default=None, init=False, repr=False)
    _hold_acquired_at: Optional[float]    = field(default=None, init=False, repr=False)
    _checkout_sent_at: Optional[float]    = field(default=None, init=False, repr=False)
    _completed_at: Optional[float]        = field(default=None, init=False, repr=False)

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Writers (write-once) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def mark_captcha_acquired(self) -> None:
        assert self._captcha_acquired_at is None, "captcha_acquired already set"
        self._captcha_acquired_at = time.monotonic()

    def mark_hold_acquired(self) -> None:
        assert self._hold_acquired_at is None, "hold_acquired already set"
        self._hold_acquired_at = time.monotonic()

    def mark_checkout_sent(self) -> None:
        assert self._checkout_sent_at is None, "checkout_sent already set"
        self._checkout_sent_at = time.monotonic()

    def mark_completed(self) -> None:
        assert self._completed_at is None, "completed already set"
        self._completed_at = time.monotonic()

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Readers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    @property
    def captcha_age(self) -> Optional[float]:
        if self._captcha_acquired_at is None:
            return None
        return time.monotonic() - self._captcha_acquired_at

    @property
    def hold_age(self) -> Optional[float]:
        if self._hold_acquired_at is None:
            return None
        return time.monotonic() - self._hold_acquired_at

    @property
    def checkout_delay(self) -> Optional[float]:
        """Elapsed since hold was acquired â€” used to enforce MAX_CHECKOUT_DELAY."""
        if self._hold_acquired_at is None:
            return None
        return time.monotonic() - self._hold_acquired_at

    @property
    def total_chain_age(self) -> float:
        return time.monotonic() - self.chain_started_at

    def to_dict(self) -> dict:
        now = time.monotonic()
        return {
            "chain_age_s":      round(now - self.chain_started_at, 3),
            "captcha_age_s":    round(now - self._captcha_acquired_at, 3) if self._captcha_acquired_at else None,
            "hold_age_s":       round(now - self._hold_acquired_at, 3) if self._hold_acquired_at else None,
            "checkout_delay_s": round(now - self._hold_acquired_at, 3) if self._hold_acquired_at else None,
        }


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Assertion helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def assert_captcha_fresh(ts: ChainTimestamps, correlation_id: str) -> None:
    """
    Verify the captcha token is within MAX_CAPTCHA_AGE.
    Raises TokenExpiredError if stale.
    """
    age = ts.captcha_age
    if age is None:
        raise TokenExpiredError(
            f"[TIMING] correlation_id={correlation_id} "
            "captcha_acquired timestamp not set â€” was mark_captcha_acquired() called?"
        )
    if age > MAX_CAPTCHA_AGE:
        msg = (
            f"[TOKEN_EXPIRED] correlation_id={correlation_id} "
            f"captcha_age={age:.1f}s > MAX_CAPTCHA_AGE={MAX_CAPTCHA_AGE}s"
        )
        logger.critical(msg)
        raise TokenExpiredError(msg)
    logger.debug(
        f"[TIMING_OK] correlation_id={correlation_id} "
        f"captcha_age={age:.1f}s (budget={MAX_CAPTCHA_AGE}s)"
    )


def assert_hold_fresh(ts: ChainTimestamps, correlation_id: str) -> None:
    """
    Verify the hold token is within MAX_HOLD_TOKEN_AGE.
    Raises TokenExpiredError if stale.
    """
    age = ts.hold_age
    if age is None:
        raise TokenExpiredError(
            f"[TIMING] correlation_id={correlation_id} "
            "hold_acquired timestamp not set â€” was mark_hold_acquired() called?"
        )
    if age > MAX_HOLD_TOKEN_AGE:
        msg = (
            f"[TOKEN_EXPIRED] correlation_id={correlation_id} "
            f"hold_age={age:.1f}s > MAX_HOLD_TOKEN_AGE={MAX_HOLD_TOKEN_AGE}s"
        )
        logger.critical(msg)
        raise TokenExpiredError(msg)
    logger.debug(
        f"[TIMING_OK] correlation_id={correlation_id} "
        f"hold_age={age:.1f}s (budget={MAX_HOLD_TOKEN_AGE}s)"
    )


def assert_checkout_window_open(ts: ChainTimestamps, correlation_id: str) -> None:
    """
    Verify we are within MAX_CHECKOUT_DELAY of hold acquisition.
    Must be called immediately before the checkout POST.
    Raises TokenExpiredError if window has closed.
    """
    delay = ts.checkout_delay
    if delay is None:
        raise TokenExpiredError(
            f"[TIMING] correlation_id={correlation_id} "
            "hold_acquired timestamp not set â€” cannot assert checkout window"
        )
    if delay > MAX_CHECKOUT_DELAY:
        msg = (
            f"[TOKEN_EXPIRED] correlation_id={correlation_id} "
            f"checkout_delay={delay:.1f}s > MAX_CHECKOUT_DELAY={MAX_CHECKOUT_DELAY}s"
        )
        logger.critical(msg)
        raise TokenExpiredError(msg)
    logger.debug(
        f"[TIMING_OK] correlation_id={correlation_id} "
        f"checkout_delay={delay:.1f}s (budget={MAX_CHECKOUT_DELAY}s)"
    )


def assert_chain_alive(ts: ChainTimestamps, correlation_id: str) -> None:
    """
    Verify the total chain has not exceeded MAX_TOTAL_CHAIN_DURATION.
    Call at the start of every stage as a defensive guard.
    """
    age = ts.total_chain_age
    if age > MAX_TOTAL_CHAIN_DURATION:
        msg = (
            f"[CHAIN_EXPIRED] correlation_id={correlation_id} "
            f"chain_age={age:.1f}s > MAX_TOTAL_CHAIN_DURATION={MAX_TOTAL_CHAIN_DURATION}s"
        )
        logger.critical(msg)
        raise TokenExpiredError(msg)
    remaining = MAX_TOTAL_CHAIN_DURATION - age
    logger.debug(
        f"[TIMING_OK] correlation_id={correlation_id} "
        f"chain_age={age:.1f}s remaining={remaining:.1f}s"
    )
