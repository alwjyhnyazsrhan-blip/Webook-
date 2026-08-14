"""
Transport Fingerprint Layer (Level 2 groundwork)
================================================

Escalation ladder:

Level 1  httpx + strict continuity             â† v6
Level 2  Playwright seeds cookies â†’ httpx executes  â† this module
Level 3  curl_cffi / tls-client JA3 impersonation   â† future
Level 4  Full Playwright transactional execution     â† last resort
"""

from .browser_seeder import BrowserSeeder
from .browser_seed_bundle import BrowserSeedBundle

__all__ = [
    "BrowserSeeder",
    "BrowserSeedBundle",
]
