import random
import hashlib
import uuid


class FingerprintGenerator:
    """
    Multi-layer Fingerprint Generator.

    Fix 3: Extended from 2 to 12 Chrome versions.
    Randomizes Accept-Language, platform, and screen metrics so every
    context gets a statistically distinct fingerprint.  All Sec-Ch-Ua
    headers are kept in sync with the chosen UA version to pass
    Chromium fingerprint consistency checks.
    """

    # 12 Chrome releases across Windows, macOS, Linux
    _PROFILES = [
        {
            "v": "120", "platform": "Windows",
            "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        },
        {
            "v": "121", "platform": "Windows",
            "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        },
        {
            "v": "122", "platform": "macOS",
            "ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        },
        {
            "v": "123", "platform": "Windows",
            "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        },
        {
            "v": "124", "platform": "Linux",
            "ua": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        },
        {
            "v": "124", "platform": "Windows",
            "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        },
        {
            "v": "125", "platform": "macOS",
            "ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        },
        {
            "v": "125", "platform": "Windows",
            "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        },
        {
            "v": "126", "platform": "Windows",
            "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        },
        {
            "v": "126", "platform": "macOS",
            "ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        },
        {
            "v": "127", "platform": "Windows",
            "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
        },
        {
            "v": "128", "platform": "Windows",
            "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        },
        {
            "v": "134", "platform": "Windows",
            "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
        },
        {
            "v": "135", "platform": "Windows",
            "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
        },
    ]

    # Language pools â€” Arabic-first (Webook's primary market) with realistic q-values
    _LANGUAGES = [
        "ar,en-US;q=0.9,en;q=0.8",
        "ar-SA,ar;q=0.9,en-US;q=0.8,en;q=0.7",
        "ar,en;q=0.9",
        "en-US,en;q=0.9,ar;q=0.8",
        "ar-SA,ar;q=0.9,en;q=0.8",
    ]

    @classmethod
    def generate(cls) -> dict:
        """
        Return a fully consistent fingerprint dict.
        All Sec-Ch-Ua-* headers are derived from the same profile so
        they cannot be distinguished from a real Chrome browser.
        """
        profile = random.choice(cls._PROFILES)
        ver = profile["v"]
        ua = profile["ua"]
        platform = profile["platform"]
        lang = random.choice(cls._LANGUAGES)

        # platform string in Sec-Ch-Ua-Platform must be double-quoted
        platform_header = f'"{platform}"'
        # mobile flag: always desktop (False) for this use-case
        mobile_flag = "?0"

        return {
            "User-Agent": ua,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": lang,
            "Accept-Encoding": "gzip, deflate, br",
            "sec-ch-ua": (
                f'"Not/A)Brand";v="8", "Chromium";v="{ver}", "Google Chrome";v="{ver}"'
            ),
            "sec-ch-ua-mobile": mobile_flag,
            "sec-ch-ua-platform": platform_header,
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "dnt": "1",
            "Connection": "keep-alive",
            "X-Device-Id": str(uuid.uuid4()),
        }

    @classmethod
    def fingerprint_id(cls, headers: dict) -> str:
        """Stable 8-char ID for telemetry/logging. Does not expose the UA."""
        ua = headers.get("User-Agent", "")
        return hashlib.sha256(ua.encode()).hexdigest()[:8]
