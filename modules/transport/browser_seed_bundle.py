"""
Browser Seed Bundle
===================

Carries Playwright-derived browser identity into httpx
without losing fingerprint continuity.
"""

from __future__ import annotations

import hashlib

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class BrowserSeedBundle:

    cookies: List[dict]

    user_agent: str

    headers: Dict[str, str]

    proxy_url: str | None

    origin: str = "playwright"

    def fingerprint_hash(self) -> str:

        raw = (
            self.user_agent
            + "|"
            + "|".join(sorted(self.headers.keys()))
            + "|"
            + str(self.proxy_url)
        )

        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def cookie_names(self) -> List[str]:
        return sorted(
            c.get("name", "")
            for c in self.cookies
        )

    def summary(self) -> dict:
        return {
            "origin": self.origin,
            "cookie_count": len(self.cookies),
            "cookie_names": self.cookie_names(),
            "fingerprint_hash": self.fingerprint_hash(),
            "proxy_present": bool(self.proxy_url),
        }
