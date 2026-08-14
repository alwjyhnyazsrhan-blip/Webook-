"""
Browser-Seeded Session  (Transport Level 2)
============================================
Problem (Level 1 ceiling)
--------------------------
httpx exposes a non-browser TLS/HTTP2 fingerprint:
  - JA3 hash that no real browser produces
  - ALPN negotiation order differs from Chrome
  - HTTP/2 SETTINGS frames with non-browser defaults
  - PRIORITY frames absent entirely
  - Pseudo-header ordering (:method, :path, :authority, :scheme) not Chrome-ordered
  - No TLS extension grease

Anti-bot stacks (Akamai Bot Manager, Cloudflare, PerimeterX) fingerprint
these at the transport layer BEFORE any cookie or header is evaluated.
This means a "correct" session identity at the application layer can still
produce:

    captcha success â†’ hold token success â†’ checkout 403/challenged

...because the TLS fingerprint changed between the captcha iframe request
(which went through a real browser) and the checkout POST (which went through
httpx).

Level 2 Strategy
-----------------
Use Playwright (real Chromium) ONLY to:
  1. Load the event page â€” acquire cloudflare clearance cookies
  2. Solve any initial challenge
  3. Extract ALL cookies from the browser's cookie jar

Then immediately:
  4. Inject those cookies into an httpx.AsyncClient
  5. Close Playwright â€” ALL subsequent requests use httpx with the seeded cookies

This gives us:
  - Real browser TLS fingerprint for the challenge clearance phase
  - httpx performance + control for the reservation execution phase
  - Cookie continuity between phases (the key invariant)

The tradeoff: we cannot guarantee the httpx JA3 matches the browser JA3
for post-seed requests.  If that becomes the failure mode, escalate to
Level 3 (curl_cffi) which can impersonate Chrome's exact TLS stack.

Usage
-----
    seeder = BrowserSeeder(proxy=proxy_url, headless=True)
    cookies = await seeder.acquire_clearance(event_slug="wwe-riyadh-2025")

    # Pass the seeded cookies into the context factory
    ctx = await create_session_context(
        ...,
        seed_cookies=cookies,
    )

    # Or inject directly into an existing client:
    seeder.inject_into_client(ctx.httpx_client, cookies)

Detection Surface Reduction
----------------------------
Even at Level 2, reduce Playwright's footprint:
  - headless=True  (but note: headless is fingerprintable)
  - Use --disable-blink-features=AutomationControlled
  - Randomise viewport, timezone, language to match httpx fingerprint headers
  - Close browser immediately after cookie extraction (< 5 s window)
  - Never re-open Playwright for the same chain; cookies persist in httpx
"""

from __future__ import annotations

import asyncio
from typing import Dict, List, Optional

import httpx

from core.logging.logger import logger
from modules.auth.fingerprint import FingerprintGenerator


class BrowserSeeder:
    """
    Acquires browser-grade cookie clearance via Playwright and exports
    the cookies for injection into an httpx.AsyncClient.

    Playwright is imported lazily so the module is importable even when
    Playwright is not installed â€” Level 1 paths never touch this class.
    """

    BASE_URL = "https://webook.com"

    def __init__(
        self,
        proxy: Optional[str] = None,
        headless: bool = True,
        fingerprint_headers: Optional[dict] = None,
    ):
        self.proxy = proxy
        self.headless = headless
        # Fingerprint used for the browser session â€” same one that will be
        # used by httpx afterwards to keep UA consistent across both layers.
        self.fingerprint = fingerprint_headers or FingerprintGenerator.generate()

    async def acquire_clearance(
        self,
        event_slug: str,
        timeout_ms: int = 20_000,
    ) -> List[Dict]:
        """
        Launch a real Chromium instance, navigate to the event page,
        wait for challenge clearance, and return the full cookie jar as
        a list of Playwright cookie dicts.

        Parameters
        ----------
        event_slug  : Webook event slug (used to construct the target URL).
        timeout_ms  : Max time (ms) to wait for page load + clearance.

        Returns
        -------
        List of cookie dicts in Playwright format:
            [{"name": "cf_clearance", "value": "...", "domain": ".webook.com", ...}, ...]

        Raises
        ------
        RuntimeError if Playwright is not installed or the page load fails.
        """
        try:
            from playwright.async_api import async_playwright, Error as PlaywrightError
        except ImportError:
            raise RuntimeError(
                "Playwright is not installed.  Run: pip install playwright && playwright install chromium"
            )

        target_url = f"{self.BASE_URL}/ar/events/{event_slug}"
        ua = self.fingerprint.get("User-Agent", "")

        logger.info(
            f"[BROWSER_SEEDER] Launching Chromium for clearance "
            f"slug={event_slug} headless={self.headless}"
        )

        async with async_playwright() as pw:
            browser_args = [
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ]
            proxy_cfg = None
            if self.proxy:
                proxy_cfg = {"server": self.proxy}

            browser = await pw.chromium.launch(
                headless=self.headless,
                args=browser_args,
                proxy=proxy_cfg,
            )
            context = await browser.new_context(
                user_agent=ua,
                locale=self._locale_from_fingerprint(),
                extra_http_headers=self._safe_headers(),
            )
            page = await context.new_page()

            try:
                await page.goto(target_url, timeout=timeout_ms, wait_until="domcontentloaded")
                # Give anti-bot checks a moment to complete
                await asyncio.sleep(2.0)
            except PlaywrightError as e:
                logger.error(f"[BROWSER_SEEDER] Navigation failed: {e}")
                await browser.close()
                raise RuntimeError(f"BrowserSeeder: page load failed: {e}")

            cookies = await context.cookies()
            await browser.close()

        logger.info(
            f"[BROWSER_SEEDER] Clearance acquired "
            f"slug={event_slug} cookie_count={len(cookies)} "
            f"names={[c['name'] for c in cookies]}"
        )
        return cookies

    def inject_into_client(
        self,
        client: httpx.AsyncClient,
        playwright_cookies: List[Dict],
    ) -> int:
        """
        Inject Playwright cookies into an httpx.AsyncClient's cookie jar.

        Translates Playwright's cookie format to httpx's format.  Only
        injects cookies whose domain matches .webook.com or webook.com to
        avoid polluting the jar with third-party tracking cookies.

        Returns the number of cookies successfully injected.
        """
        ALLOWED_DOMAINS = {".webook.com", "webook.com", "api.webook.com", "payments.webook.com"}
        injected = 0

        for cookie in playwright_cookies:
            domain  = cookie.get("domain", "")
            name    = cookie.get("name", "")
            value   = cookie.get("value", "")
            path    = cookie.get("path", "/")

            # Skip third-party / analytics cookies
            if not any(domain.endswith(d.lstrip(".")) for d in ALLOWED_DOMAINS):
                continue

            try:
                client.cookies.set(name, value, domain=domain.lstrip("."), path=path)
                injected += 1
            except Exception as e:
                logger.warning(f"[BROWSER_SEEDER] Cookie inject failed: name={name} err={e}")

        logger.info(
            f"[BROWSER_SEEDER] Injected {injected}/{len(playwright_cookies)} cookies into httpx client"
        )
        return injected

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ Private helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def _locale_from_fingerprint(self) -> str:
        lang = self.fingerprint.get("Accept-Language", "ar,en-US;q=0.9")
        # Extract primary language tag for Playwright's locale param
        primary = lang.split(",")[0].split(";")[0].strip()
        return primary if primary else "ar"

    def _safe_headers(self) -> dict:
        """
        Headers to pass as extra_http_headers to Playwright context.
        Only include headers that Playwright won't override itself.
        Exclude User-Agent (handled via new_context user_agent param).
        """
        exclude = {"user-agent", "accept", "accept-encoding"}
        return {
            k: v for k, v in self.fingerprint.items()
            if k.lower() not in exclude
        }
