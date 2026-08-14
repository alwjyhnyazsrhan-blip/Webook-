"""
Per-Account Locking  (Fix 4)
============================
Prevents two concurrent reservation tasks from using the same Webook account
at the same time.  A race between two tasks sharing one bearer token would cause
both holds to fail (the API rejects duplicate active sessions).

Usage
-----
    async with account_lock_manager.acquire(account_id):
        # only one task per account_id runs here at once
        ctx = await create_session_context(...)
        result = await run_reservation_chain(ctx, ...)

Design notes
------------
- Locks are held for the entire reservation chain lifecycle.
- Lock objects are created lazily and cached in a WeakValueDictionary so that
  locks for idle accounts are garbage-collected automatically.
- All state is in-process; for multi-process deployments replace the asyncio
  locks with a Redis SET-based distributed mutex.
"""

import asyncio
import weakref
from contextlib import asynccontextmanager
from core.logging.logger import logger


class AccountLockManager:
    """
    Registry of per-account asyncio.Lock objects.
    Thread-safe within a single event loop (Python's asyncio guarantee).
    """

    def __init__(self):
        # WeakValueDictionary: entries disappear once no coroutine holds the lock
        self._locks: weakref.WeakValueDictionary = weakref.WeakValueDictionary()
        self._registry_lock = asyncio.Lock()   # guards _locks mutations

    def _get_or_create(self, account_id: str) -> asyncio.Lock:
        """Return the existing lock or create a new one (not thread-safe alone)."""
        lock = self._locks.get(account_id)
        if lock is None:
            lock = asyncio.Lock()
            self._locks[account_id] = lock
        return lock

    @asynccontextmanager
    async def acquire(self, account_id: str, timeout: float = 300.0):
        """
        Async context manager.  Acquires the per-account lock with an optional
        `timeout` (seconds).  Raises asyncio.TimeoutError if the lock cannot
        be acquired within the budget â€” callers should treat this as a
        RETRYING signal.

        Parameters
        ----------
        account_id : str
            Unique account identifier (matches ReservationTask.account_id).
        timeout : float
            Max seconds to wait for the lock before raising TimeoutError.
        """
        async with self._registry_lock:
            lock = self._get_or_create(account_id)

        logger.info(f"[ACCOUNT_LOCK] Attempting acquire for account_id={account_id}")
        try:
            acquired = await asyncio.wait_for(lock.acquire(), timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning(
                f"[ACCOUNT_LOCK] Timeout waiting for account_id={account_id} "
                f"(timeout={timeout}s) â€” marking as RETRYING"
            )
            raise

        logger.info(f"[ACCOUNT_LOCK] Acquired for account_id={account_id}")
        try:
            yield
        finally:
            lock.release()
            logger.info(f"[ACCOUNT_LOCK] Released for account_id={account_id}")

    def active_count(self) -> int:
        """Number of accounts currently holding a lock (for monitoring)."""
        return sum(1 for lock in self._locks.values() if lock.locked())


# Module-level singleton â€” import and use directly
account_lock_manager = AccountLockManager()
