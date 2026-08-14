import asyncio
import gzip
import json
import re
import random
import ssl
import uuid
import httpx
from core.logging.logger import logger
from modules.auth.fingerprint import FingerprintGenerator
from modules.session.snapshots import RequestSnapshot, global_snapshot_store
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from modules.session.context import ReservationSessionContext

class WebookApiClient:
    BASE_URL = "https://api.webook.com/api/v2"
    AUTH_URL = "https://api.webook.com/api/v2"
    PAYMENT_URL = "https://payments.webook.com/api/v2"
    APP_SOURCE = "webook"

    # Fallback/Legacy list - now used as a bootstrap, not a hard limit
    KNOWN_ORGS = [
        "riyadh-season", "jeddah-season", "diriyah-season", "neom",
        "al-shabab", "al-ahli", "al-ettifaq", "al-fateh", "al-okhdood",
        "al-kholood", "al-hazem", "general-entertainment-authority", "saudi-pro-league",
        "mdl-beast", "esports-world-cup", "balad-beast", "wwe", "saudia",
        "red-sea-international-film-festival", "alula", "roshn", "ithra",
        "ministry-of-culture", "saudi-esports-federation", "taif-season",
        "aseer-season", "hail-season", "webook", "al-nassr", "al-hilal",
        "al-ittihad", "al-qadsiah", "al-raed", "al-khaleej", "al-orubah",
        "al-riyadh", "al-weihda",
    ]

    def __init__(
        self,
        bearer_token: str = None,
        proxy: str = None,
        account_id: str = "default",
        headers: dict = None,
        http_client: "httpx.AsyncClient | None" = None,
        session_ctx: "Optional[ReservationSessionContext]" = None,
    ):
        self.bearer_token = bearer_token
        self.account_id = str(account_id)
        self.proxy_url = proxy
        self.proxy = {"http://": proxy, "https://": proxy} if proxy else None
        self._headers = headers or FingerprintGenerator.generate()
        self._api_token = None
        try:
            from core.config.settings import settings as app_settings
            self._api_token = app_settings.webook_api_token
        except Exception:
            self._api_token = "ce492c7f756978ba98da0627544f69fbc76aae789bdab3f241d111d8642416db"

        # BLU device token — needed for /register-login and /accessibility-profile-request (spec p.7)
        self._blu_token = None
        try:
            from core.config.settings import settings as app_settings
            self._blu_token = getattr(app_settings, "login_device_token", None)
        except Exception:
            pass
        if not self._blu_token:
            self._blu_token = "bqvtwD2zBdLC8HkUIsvwmlhMnkfifLtffml2mNNRevDnb25yn5Axw2zqtwB8zvB0"

        # TLS cipher suite tuned for reliable webook.com TLS handshake (from partner project)
        self._ssl_ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        self._ssl_ctx.set_ciphers(
            "ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:"
            "ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:"
            "ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:"
            "DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384"
        )
        self._ssl_ctx.set_alpn_protocols(['h2', 'http/1.1'])

        # Fix 1: store the injected client.  When provided (reservation path),
        # _request uses it directly and never touches NetworkManager.
        # When None (standalone / test path), _request falls back to NetworkManager
        # so existing non-reservation callers continue working without changes.
        self._injected_client: "httpx.AsyncClient | None" = http_client
        self._session_ctx: "Optional[ReservationSessionContext]" = session_ctx

    def _rotate_fingerprint(self):
        self._headers = FingerprintGenerator.generate()

    def _derive_stage_name(self, url: str) -> str:
        url_lower = url.lower()
        if "hold-token" in url_lower or "/hold" in url_lower:
            return "hold_token"
        if "/checkout" in url_lower:
            return "checkout"
        if "captcha" in url_lower or "turnstile" in url_lower:
            return "captcha_verification"
        if "/events/" in url_lower:
            return "event_detail"
        return "general"

    def _build_headers(self, authenticated: bool = False, url: Optional[str] = None) -> dict:
        """
        Builds a high-fidelity, domain-aware header set.
        Prevents internal token leakage to third-party domains (SeatCloud).
        """
        is_webook = "webook.com" in (url or "")
        path = url.split("webook.com")[-1] if (url and is_webook) else ""
        
        # Path-based token switching (BLU token required for register-login/accessibility)
        _BLU_PATHS = ("/register-login", "/accessibility-profile", "/accessibility-profile-request")
        
        device_token = (
            self._blu_token 
            if any(p in path for p in _BLU_PATHS)
            else (self._api_token or "ce492c7f756978ba98da0627544f69fbc76aae789bdab3f241d111d8642416db")
        )

        # Base structure
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9,ar-SA;q=0.8,ar;q=0.7",
            "Content-Type": "application/json",
            "Origin": "https://webook.com",
            "X-Requested-With": "XMLHttpRequest", # Mandatory for Webook XHR
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site" if is_webook else "cross-site",
            **self._headers, # Fingerprint: UA, sec-ch-ua-*, etc.
        }

        # DOMAIN-AWARE SANITIZATION: Do not leak Webook headers to SeatCloud
        if is_webook:
            headers["token"] = device_token
            headers["X-Client-Version"] = "1.4.82"
            headers["X-App-Version"] = "1.4.82"
            headers["Referer"] = "https://webook.com/en"
        else:
            # For SeatCloud/Seats.io
            # Tighten referer to include the base event path to avoid 'Shallow Referer' detection
            headers["Referer"] = "https://webook.com/en" 

        # TELEMETRY MOCKING: Simulate browser interaction flow
        if url:
            url_lower = url.lower()
            if "checkout" in url_lower or "hold" in url_lower:
                headers["Sec-Fetch-User"] = "?1"
                headers["Sec-Fetch-Mode"] = "cors"
                headers["Sec-Fetch-Dest"] = "empty"
                if "/event-seat/checkout" in url_lower and is_webook:
                    slug_match = re.search(r"/event-detail/([^/]+)/event-seat/checkout", url_lower)
                    current_slug = slug_match.group(1) if slug_match else "event"
                    headers["Referer"] = f"https://webook.com/en/events/{current_slug}/book-tickets"
            
            if is_webook and "/events/" in url:
                slug_match = re.search(r"/events/([^/?]+)", url)
                if slug_match:
                    headers["Referer"] = f"https://webook.com/ar/events/{slug_match.group(1)}"

        if authenticated and self.bearer_token and is_webook:
            headers["Authorization"] = f"Bearer {self.bearer_token}"

        return headers

    async def _request(self, method: str, url: str, authenticated: bool = False, **kwargs) -> httpx.Response:
        # Fix 1: prefer the injected client (reservation path) to avoid NetworkManager
        if self._injected_client is not None:
            client = self._injected_client
        else:
            # Fallback: standalone / background callers not in a reservation context
            from core.network.session import network_manager
            client = await network_manager.get_client(session_id=self.account_id, proxy=self.proxy_url)

        if self._session_ctx is not None:
            stage_name = self._derive_stage_name(url)
            self._session_ctx.assert_identity_intact(stage=stage_name)

        headers = self._build_headers(authenticated=authenticated, url=url)
        if "headers" in kwargs:
            headers.update(kwargs.pop("headers"))
        try:
            response = await client.request(method, url, headers=headers, **kwargs)

            snap = RequestSnapshot.capture(
                stage=self._derive_stage_name(url),
                method=method,
                url=url,
                headers=headers,
                body=kwargs.get("json"),
                response_code=response.status_code,
                response_headers=dict(response.headers),
            )

            corr_id = (
                self._session_ctx.correlation_id
                if self._session_ctx
                else self.account_id
            )

            drift = global_snapshot_store.record_and_detect(
                snap=snap,
                correlation_id=corr_id,
            )

            if self._session_ctx is not None:
                self._session_ctx.record_snapshot(snap)

            if drift:
                severity_tag = f"[SHAPE_DRIFT/{drift.severity}]"
                logger.warning(
                    f"{severity_tag} "
                    f"correlation_id={corr_id} "
                    f"url={url} "
                    f"stage={drift.stage} "
                    f"severity={drift.severity} "
                    f"baseline_code={drift.baseline_code} "
                    f"current_code={drift.current_code} "
                    f"added_headers={drift.added_headers} "
                    f"removed_headers={drift.removed_headers} "
                    f"added_body_keys={drift.added_body_keys} "
                    f"removed_body_keys={drift.removed_body_keys}"
                )

            return response
        except httpx.HTTPError as e:
            logger.error(f"WebookAPI Request Failure: {method} {url} | {e}")
            raise

    async def simulate_human_arrival(self, slug: str):
        try:
            await self._request("GET", f"https://webook.com/ar/events/{slug}", authenticated=False)
            await asyncio.sleep(max(0.8, random.gauss(1.5, 0.5)))
        except Exception:
            return

    async def _simulate_interaction(self, action: str):
        if action == "map_interaction":
            wait = max(0.3, random.gauss(0.8, 0.3))
        elif action == "seat_click":
            wait = max(0.15, random.gauss(0.4, 0.15))
        else:
            wait = max(0.1, random.gauss(0.5, 0.2))
        await asyncio.sleep(wait)

    async def get_events_by_organization(
        self, org_slug: str, lang: str = "ar", status: str = "upcoming",
        page: int = 1, per_page: int = 50, season_slug: str = None,
        team_slug: str = None, event_type: str = None,
        exhaustive: bool = False,
        category: str = None, city: str = None,
        date_from: str = None, date_to: str = None,
    ) -> dict:
        # FIX: Official API endpoint is /filter/events/{organizationSlug} (section 4.1)
        # with query params: lang*, category, city, date_from, date_to, page, per_page
        params = {
            "lang": lang,
            "page": str(page),
            "per_page": str(per_page),
        }
        if category:
            params["category"] = category
        if city:
            params["city"] = city
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to
        # Legacy passthrough params (may be ignored by server but kept for compat)
        if season_slug:
            params["season_slug"] = season_slug
        if team_slug:
            params["team_slug"] = team_slug
        if event_type:
            params["event_type"] = event_type
        if status:
            params["status"] = status

        try:
            # FIX: Primary endpoint per official spec (section 4.1)
            url = f"{self.BASE_URL}/filter/events/{org_slug}"
            resp = await self._request("GET", url, params=params)
            # Fallback to legacy orgs endpoint if primary fails
            if resp.status_code == 404:
                url = f"{self.BASE_URL}/organizations/{org_slug}/events"
                resp = await self._request("GET", url, params=params)
            if resp.status_code != 200:
                return {"events": [], "seasons": [], "total": 0}

            data = resp.json()
            page_data = data.get("data", {})
            if not isinstance(page_data, dict): page_data = {}
            
            all_events = page_data.get("data", [])
            total = page_data.get("total", 0)
            
            if exhaustive and total > per_page:
                current_p = page + 1
                while len(all_events) < total:
                    params["page"] = str(current_p)
                    r = await self._request("GET", url, params=params)
                    if r.status_code != 200: break
                    d = r.json().get("data", {})
                    evs = d.get("data", [])
                    if not evs: 
                        break
                    
                    # Prevent duplicates and infinite loop if API returns same data
                    new_count = 0
                    for ev in evs:
                        ev_id = str(ev.get("_id") or ev.get("id") or "")
                        if ev_id not in [str(x.get("_id") or x.get("id") or "") for x in all_events]:
                            all_events.append(ev)
                            new_count += 1
                    
                    if new_count == 0:
                        break
                        
                    current_p += 1
                    if current_p > 20: # Higher safety cap
                        break

            return {
                "events": all_events,
                "seasons": data.get("seasons", []),
                "total": total,
                "per_page": per_page,
                "current_page": page,
            }
        except Exception as e:
            logger.error(f"WebookClient: get_events_by_organization failed: {e}")
            return {"events": [], "seasons": [], "total": 0}

    async def get_all_upcoming_events(self, lang: str = "ar", page: int = 1, per_page: int = 50, exhaustive: bool = False, orgs: list = None) -> dict:
        all_events = []
        seen = set()
        sync_orgs = orgs if orgs else self.KNOWN_ORGS
        
        # Parallelize organization fetching
        sem = asyncio.Semaphore(10)
        
        async def _fetch_org(org_slug):
            async with sem:
                try:
                    current_page = page
                    org_events = []
                    while True:
                        result = await self.get_events_by_organization(
                            org_slug, lang=lang, status="upcoming", page=current_page, per_page=per_page, exhaustive=exhaustive
                        )
                        events = result.get("events", [])
                        for ev in events:
                            ev_id = str(ev.get("_id") or ev.get("id") or "")
                            if ev_id:
                                org_events.append(ev)
                        
                        if not exhaustive or not events or len(events) < per_page:
                            break
                        current_page += 1
                        if current_page > 5: break # Cap for global scan
                    return org_events
                except Exception:
                    return []

        results = await asyncio.gather(*[_fetch_org(org) for org in sync_orgs], return_exceptions=True)
        for res in results:
            if isinstance(res, list):
                for ev in res:
                    ev_id = str(ev.get("_id") or ev.get("id") or "")
                    if ev_id and ev_id not in seen:
                        seen.add(ev_id)
                        all_events.append(ev)
                        
        return {"events": all_events, "total": len(all_events)}

    async def search_events(self, query: str, lang: str = "ar") -> list:
        params = {"lang": lang, "query": query}
        try:
            # Webook search endpoint is often /events/search or /search
            resp = await self._request("GET", f"{self.BASE_URL}/events/search", params=params)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("data", []) if isinstance(data.get("data"), list) else []
            
            # Fallback to general search
            resp = await self._request("GET", f"{self.BASE_URL}/search", params=params)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("data", []) if isinstance(data.get("data"), list) else []
                
            return []
        except Exception as e:
            logger.error(f"WebookClient: search_events failed: {e}")
            return []

    async def get_organizations(self, lang: str = "ar", page: int = 1, limit: int = 100,
                               sport_slug: str = None, sport: str = None) -> dict:
        # FIX: Official API spec (section 5.2) uses 'limit' (not 'per_page') and supports sport_slug/sport filters
        params = {"lang": lang, "page": str(page), "limit": str(limit)}
        if sport_slug:
            params["sport_slug"] = sport_slug
        if sport:
            params["sport"] = sport
        # /organizations is the canonical endpoint per spec section 5.2
        try:
            resp = await self._request("GET", f"{self.BASE_URL}/organizations", params=params)
            if resp.status_code == 200:
                data = resp.json()
                return data if isinstance(data, dict) else {}
        except Exception as e:
            logger.error(f"WebookClient: get_organizations failed: {e}")
        return {"data": {"data": []}}

    async def get_genres(self, lang: str = "ar") -> list:
        """Fetches all event categories/genres from the API."""
        try:
            # Webook often returns genres in the landing or discovery response
            resp = await self._request("GET", f"{self.BASE_URL}/home", params={"lang": lang})
            if resp.status_code == 200:
                data = resp.json()
                genres = data.get("genres") or data.get("categories") or []
                if genres: return genres
            
            # Fallback 2: Check discovery endpoint
            resp = await self._request("GET", f"{self.BASE_URL}/explore", params={"lang": lang})
            if resp.status_code == 200:
                data = resp.json()
                return data.get("genres") or data.get("categories") or []
        except Exception as e:
            logger.error(f"WebookClient: get_genres failed: {e}")
        return []

    async def get_events_by_genre(self, genre_slug: str, lang: str = "ar", page: int = 1, per_page: int = 50) -> dict:
        params = {"lang": lang, "page": str(page), "per_page": str(per_page), "status": "upcoming"}
        try:
            url = f"{self.BASE_URL}/genres/{genre_slug}/events"
            resp = await self._request("GET", url, params=params)
            if resp.status_code == 200:
                return resp.json()
            
            # Fallback: Many sites use /categories/
            url = f"{self.BASE_URL}/categories/{genre_slug}/events"
            resp = await self._request("GET", url, params=params)
            return resp.json() if resp.status_code == 200 else {}
        except Exception:
            return {}

    async def get_me(self) -> dict:
        """
        Fetches current user profile. Uses /user/profile (section 10.2) per official API spec.
        The legacy /me endpoint is NOT in the spec.
        """
        url = f"{self.BASE_URL}/user/profile"  # FIX: spec §10.2 is /user/profile, not /me
        try:
            resp = await self._request("GET", url, authenticated=True)
            logger.info(f"[API_FETCH] name=get_me status={resp.status_code}")
            return resp.json()
        except Exception as e:
            logger.error(f"[API_EXCEPTION] name=get_me error={e}")
            return {"status": "error", "message": str(e), "_http_status": 500}

    async def get_event_detail(self, slug: str, lang: str = "ar") -> dict:
        try:
            # Matches browser URL: https://api.webook.com/api/v2/event-detail/{slug}
            resp = await self._request("GET", f"{self.BASE_URL}/event-detail/{slug}", params={"lang": lang, "visible_in": "rs"})
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            logger.warning(f"get_event_detail({slug}) returned {e.response.status_code}: {e.response.text[:200]}")
            raise
        except Exception as e:
            logger.error(f"WebookClient: get_event_detail failed: {e}")
            raise

    async def get_event_details(self, slug: str, lang: str = "ar") -> dict:
        return await self.get_event_detail(slug, lang=lang)

    async def get_event_tickets(self, slug: str, lang: str = "ar", page: int = 1) -> dict:
        try:
            resp = await self._request("GET", f"{self.BASE_URL}/event-ticket-details/{slug}", params={"lang": lang, "visible_in": "rs", "page": str(page)})
            if resp.status_code == 200:
                data = resp.json().get("data", {})
                tickets = data.get("event_ticket") or data.get("event_tickets") or []
                return {"event_tickets": tickets, "data": data}
            return {"event_tickets": [], "data": {}, "_http_status": resp.status_code}
        except Exception as e:
            logger.error(f"WebookClient: get_event_tickets failed: {e}")
            return {"event_tickets": [], "data": {}, "error": str(e)}

    async def get_timeslot_capacity(self, slug: str, time_slot_id: str, lang: str = "ar") -> dict:
        try:
            resp = await self._request("GET", f"{self.BASE_URL}/events/{slug}", params={"lang": lang, "time_slot": time_slot_id})
            return resp.json().get("data", {}) if resp.status_code == 200 else {}
        except Exception as e:
            logger.error(f"WebookClient: get_timeslot_capacity failed: {e}")
            return {}

    async def get_event_availability(self, slug: str, lang: str = "ar") -> dict:
        try:
            resp = await self._request("GET", f"{self.BASE_URL}/events/{slug}", params={"lang": lang})
            if resp.status_code == 200:
                data = resp.json().get("data", {})
                return {
                    "event_tickets": data.get("event_tickets", []),
                    "is_soldout": data.get("is_soldout", False),
                    "is_seated": data.get("is_seated", False),
                    "data": data,
                }
            return {"_http_status": resp.status_code, "body": resp.text[:500]}
        except Exception as e:
            logger.error(f"[API_EXCEPTION] name=get_event_availability error={e}")
            return {"_http_status": 500, "message": str(e)}

    async def get_tournament_detail(self, slug: str, lang: str = "ar") -> dict:
        params = {"lang": lang}
        try:
            resp = await self._request("GET", f"{self.BASE_URL}/event-tournaments/{slug}", params=params)
            return resp.json().get("data", {}) if resp.status_code == 200 else {}
        except Exception as e:
            logger.error(f"WebookClient: get_tournament_detail failed: {e}")
            return {}

    async def get_tournament_events(self, slug: str, lang: str = "ar", page: int = 1, per_page: int = 20, venue: str = None, team: str = None) -> dict:
        params = {"lang": lang, "page": str(page), "per_page": str(per_page)}
        if venue:
            params["venue"] = venue
        if team:
            params["team"] = team
        try:
            resp = await self._request("GET", f"{self.BASE_URL}/event-tournaments/{slug}/events", params=params)
            return resp.json() if resp.status_code == 200 else {}
        except Exception as e:
            logger.error(f"WebookClient: get_tournament_events failed: {e}")
            return {}

    async def get_team_events(
        self, team_id: str, org_slug: str = None, lang: str = "ar",
        status: str = "upcoming_ongoing", per_page: int = 20,
    ) -> dict:
        # FIX: Official API endpoint is /team/{teamId}/events (section 7.3)
        # Status enum: all, upcoming_ongoing, ongoing, past  (NOT "upcoming")
        _VALID_STATUSES = {"all", "upcoming_ongoing", "ongoing", "past"}
        # Map legacy 'upcoming' → 'upcoming_ongoing' to avoid 422 validation error
        if status not in _VALID_STATUSES:
            status = "upcoming_ongoing"
        params: dict = {"lang": lang, "status": status, "per_page": str(per_page)}
        if org_slug:
            params["organization_slug"] = org_slug
        try:
            resp = await self._request("GET", f"{self.BASE_URL}/team/{team_id}/events", params=params)
            return resp.json() if resp.status_code == 200 else {}
        except Exception as e:
            logger.error(f"WebookClient: get_team_events failed: {e}")
            return {}

    async def get_organization_detail(self, slug: str, lang: str = "ar") -> dict:
        params = {"lang": lang}
        try:
            resp = await self._request("GET", f"{self.BASE_URL}/organizations/{slug}", params=params)
            return resp.json().get("data", {}) if resp.status_code == 200 else {}
        except Exception as e:
            logger.error(f"WebookClient: get_organization_detail failed: {e}")
            return {}

    async def get_organization_events(self, slug: str, lang: str = "ar", page: int = 1) -> dict:
        params = {"lang": lang, "page": str(page), "per_page": "20"}
        try:
            resp = await self._request("GET", f"{self.BASE_URL}/organizations/{slug}/events", params=params)
            return resp.json() if resp.status_code == 200 else {}
        except Exception as e:
            logger.error(f"WebookClient: get_organization_events failed: {e}")
            return {}

    async def get_user_profile(self, lang: str = "ar") -> dict:
        try:
            resp = await self._request("GET", f"{self.AUTH_URL}/user/profile", params={"lang": lang}, authenticated=True)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("data", data)
            logger.warning(f"[API_RESPONSE] name=get_user_profile status={resp.status_code} body={resp.text[:500]}")
            return {}
        except Exception as e:
            logger.error(f"WebookClient: get_user_profile failed: {e}")
            return {}

    async def get_user_bookings(self, lang: str = "ar", page: int = 1, status: str = None) -> dict:
        params = {"lang": lang, "page": str(page), "per_page": "20", "hide_vapps": "true", "show_payment_link": "true"}
        if status:
            params["event_status"] = status
        try:
            resp = await self._request("GET", f"{self.BASE_URL}/user/bookings", params=params, authenticated=True)
            return resp.json() if resp.status_code == 200 else {}
        except Exception as e:
            logger.error(f"WebookClient: get_user_bookings failed: {e}")
            return {}

    def _checkout_order(self, event_id: str, tickets: list = None, lang: str = "ar", payment_method: str = "credit_card", extra: dict = None) -> dict:
        order = {
            "event_id": event_id,
            "redirect": f"https://webook.com/{lang}/payment-success",
            "redirect_failed": f"https://webook.com/{lang}/payment-failed",
            "booking_source": "rs-web",  # FIX: was "web" — browser sends "rs-web"
            "app_source": "rs",           # FIX: was "webook" — browser sends "rs"
            "lang": lang,
            "payment_method": payment_method,
            "is_wallet": False,
            "refund_guarantee": False,
        }
        if tickets is not None:
            order["tickets"] = tickets
        if extra:
            order.update({k: v for k, v in extra.items() if v is not None})
        return order

    async def hold_token(self, slug: str, event_id: str = None, time_slot_id: str = None, lang: str = "ar", captcha_token: str = None, operation_uuid: str = None) -> dict:
        """Hold token for EVENT seated checkout (section 3.1)."""
        endpoints = [
            f"{self.BASE_URL}/event-detail/{slug}/hold-token",
            f"{self.BASE_URL}/event-detail/{slug}/hold",
            f"{self.BASE_URL}/reservations/hold",
        ]
        payload: dict = {"lang": lang}
        if event_id:
            # FIX: field name is event_id* per spec section 3.1
            payload["event_id"] = event_id
        if time_slot_id:
            payload["time_slot_id"] = time_slot_id
        if captcha_token:
            # FIX: Official API spec (section 3.1) uses field name 'turnstile', not 'cf-turnstile-response'
            payload["turnstile"] = captcha_token
            
        custom_headers = {}
        if operation_uuid:
            custom_headers["X-Operation-ID"] = operation_uuid

        for url in endpoints:
            try:
                logger.info(f"[API_FETCH] name=hold_token method=POST url={url} payload={payload}")
                resp = await self._request("POST", url, authenticated=True, json=payload, headers=custom_headers)
                logger.warning(
                    f"[HOLD_TOKEN_RESPONSE] "
                    f"status={resp.status_code} "
                    f"body={resp.text[:1000]}"
                )
                data = resp.json()
                if isinstance(data, dict):
                    data["_http_status"] = resp.status_code
                
                # STRICT: Immediately return 422 - DO NOT continue retries
                if resp.status_code == 422:
                    logger.warning(
                        f"[HOLD_TOKEN_422] "
                        f"endpoint={url} "
                        f"body={resp.text[:1000]}"
                    )
                    return data
                
                result = data.get("data", {}) if data.get("status") == "success" else data
                if isinstance(result, dict):
                    has_token = bool(
                        result.get("hold_token") or result.get("holdToken")
                        or result.get("token") or result.get("id")
                        or result.get("holdId")
                    )
                    if not has_token and result.get("_id") and result.get("address"):
                        logger.warning(f"[HOLD_TOKEN_ENDPOINT_RETURNED_EVENT] url={url} returned event detail")
                        continue
                if resp.status_code == 200 and has_token:
                    return result
                if resp.status_code == 401:
                    logger.warning(f"[HOLD_TOKEN_401] endpoint={url} - continuing to next endpoint")
                    continue
                logger.warning(f"[HOLD_TOKEN_FAILED] endpoint={url} status={resp.status_code} - continuing to next endpoint")
                continue
            except Exception as e:
                logger.warning(f"[HOLD_TOKEN_ERROR] endpoint={url} error={e} - continuing to next endpoint")
                continue
        
        logger.error(f"[API_EXCEPTION] name=hold_token all endpoints failed")
        return {"status": "error", "message": "All hold-token endpoints failed", "_http_status": 500}

    async def hold_token_season(self, slug: str, season_id: str, lang: str = "ar") -> dict:
        """Hold token for SEASON seated checkout (section 4.7).
        Body: { season_id*: str, lang*: enum }
        """
        url = f"{self.BASE_URL}/season-detail/{slug}/hold-token"
        payload = {"season_id": season_id, "lang": lang}  # season_id* required (not event_id)
        try:
            logger.info(f"[API_FETCH] name=hold_token_season method=POST url={url} payload={payload}")
            resp = await self._request("POST", url, authenticated=True, json=payload)
            logger.info(f"[HOLD_TOKEN_SEASON_RESPONSE] status={resp.status_code} body={resp.text[:500]}")
            data = resp.json()
            if isinstance(data, dict):
                data["_http_status"] = resp.status_code
            result = data.get("data", {}) if data.get("status") == "success" else data
            return result
        except Exception as e:
            logger.error(f"[API_EXCEPTION] name=hold_token_season error={e}")
            return {"status": "error", "message": str(e), "_http_status": 500}

    async def checkout_season_seated(
        self, slug: str, seats: list, hold_token: str,
        season_id: str = None, lang: str = "ar",
        payment_method: str = "card",  # FIX: season spec enum is 'card' NOT 'credit_card' (section 4.8)
        redirect: str = None, redirect_failed: str = None,
    ) -> dict:
        """Season seated checkout (section 4.8).
        selectedSeats items: { id, label, holdToken, categoryKey (string) }
        hold_token* is a top-level field (not holdToken)
        payment_method enum: card, apple_pay, stc_pay, mada
        """
        # FIX: season payment_method values differ from event: 'card' not 'credit_card'
        _SEASON_PAYMENT_METHODS = {"card", "apple_pay", "stc_pay", "mada"}
        if payment_method not in _SEASON_PAYMENT_METHODS:
            payment_method = "card"  # safe default for seasons

        # Format seats per spec 4.8: { id, label, holdToken, categoryKey: string }
        api_seats = [
            {
                "id": s.get("id"),
                "label": s.get("label"),
                "holdToken": hold_token,                         # per-seat holdToken field
                "categoryKey": str(s.get("categoryKey", "")),   # FIX: string for seasons
            }
            for s in (seats or [])
        ]

        payload = {
            "selectedSeats": api_seats,
            "hold_token": hold_token,   # FIX: top-level field is hold_token* (not holdToken)
            "payment_method": payment_method,
            "lang": lang,
            "redirect": redirect or f"https://webook.com/{lang}/payment-success",
            "redirect_failed": redirect_failed or f"https://webook.com/{lang}/payment-failed",
        }
        if season_id:
            payload["season_id"] = season_id

        url = f"{self.BASE_URL}/season-detail/{slug}/season-seat/checkout"
        logger.info(f"[SEASON_CHECKOUT_PAYLOAD] url={url} payload_preview={str(payload)[:400]}")
        try:
            resp = await self._request("POST", url, authenticated=True, json=payload)
            logger.info(f"[SEASON_CHECKOUT_RESPONSE] status={resp.status_code} body={resp.text[:500]}")
            data = resp.json()
            if isinstance(data, dict):
                data["_http_status"] = resp.status_code
            return data
        except Exception as e:
            logger.error(f"[API_EXCEPTION] name=checkout_season_seated error={e}")
            return {"status": "error", "message": str(e), "_http_status": 500}

    async def checkout(self, slug: str, order: dict, lang: str = "ar", is_season: bool = False) -> dict:
        prefix = "season-detail" if is_season else "event-detail"
        url = f"{self.BASE_URL}/{prefix}/{slug}/checkout"
        order["lang"] = lang
        order["app_source"] = self.APP_SOURCE
        try:
            resp = await self._request("POST", url, json=order, authenticated=True)
            data = resp.json()
            if isinstance(data, dict):
                data["_http_status"] = resp.status_code
            return data
        except Exception as e:
            logger.error(f"WebookClient: checkout failed: {e}")
            return {"status": "error", "message": str(e), "_http_status": 500}

    async def checkout_plain(self, slug: str, event_id: str, tickets: list, lang: str = "ar", payment_method: str = "credit_card", time_slot_id: str = None, operation_uuid: str = None) -> dict:
        payload = self._checkout_order(
            event_id=event_id,
            tickets=tickets,
            lang=lang,
            payment_method=payment_method,
            extra={"time_slot_id": time_slot_id},
        )
        logger.info(f"[CHECKOUT_PAYLOAD] tickets_raw={tickets}")
        logger.info(f"[CHECKOUT_PAYLOAD] full_payload={payload}")
        url = f"{self.BASE_URL}/event-detail/{slug}/checkout"  # FIX: removed ?lang= — lang is already in the JSON body
        
        headers = self._build_headers(authenticated=True)
        final_headers = {**headers, "Authorization": f"Bearer {self.bearer_token}"}
        
        if operation_uuid:
            final_headers["Idempotency-Key"] = operation_uuid
            final_headers["X-Operation-ID"] = operation_uuid
        
        logger.info("=" * 80)
        logger.info("[CHECKOUT_PLAIN_FULL_REQUEST] >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        logger.info(f"[CHECKOUT_ENDPOINT] {url}")
        logger.info(f"[CHECKOUT_METHOD] POST")
        safe_headers = {k: v for k, v in final_headers.items() if k != 'Authorization' and k != 'User-Agent'}
        logger.info(f"[CHECKOUT_HEADERS] {json.dumps(safe_headers, ensure_ascii=False)}")
        logger.info(f"[CHECKOUT_AUTH] Bearer {self.bearer_token[:20]}..." if self.bearer_token else "[CHECKOUT_AUTH] None")
        logger.info(f"[CHECKOUT_PAYLOAD] {json.dumps(payload, ensure_ascii=False)}")
        logger.info("[CHECKOUT_PLAIN_FULL_REQUEST] <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
        logger.info("=" * 80)
        
        try:
            resp = await self._request("POST", url, authenticated=True, json=payload)
            
            # FULL RESPONSE CONTEXT
            logger.info("=" * 80)
            logger.info("[CHECKOUT_PLAIN_FULL_RESPONSE] >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
            logger.info(f"[CHECKOUT_STATUS] {resp.status_code}")
            logger.info(f"[CHECKOUT_STATUS_TEXT] {resp.reason_phrase}")
            logger.info(f"[CHECKOUT_RESPONSE_HEADERS] {dict(resp.headers)}")
            logger.info(f"[CHECKOUT_RAW_BODY] {resp.text}")
            logger.info(f"[CHECKOUT_RESPONSE_CONTENT_LENGTH] {len(resp.content)}")
            
            # Extract correlation IDs if present
            correlation_ids = {
                "x-request-id": resp.headers.get("x-request-id"),
                "x-correlation-id": resp.headers.get("x-correlation-id"),
                "request-id": resp.headers.get("request-id"),
                "trace-id": resp.headers.get("trace-id"),
            }
            logger.info(f"[CHECKOUT_CORRELATION_IDS] {json.dumps(correlation_ids)}")
            logger.info("[CHECKOUT_PLAIN_FULL_RESPONSE] <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
            logger.info("=" * 80)
            
            data = resp.json()
            if isinstance(data, dict):
                data["_http_status"] = resp.status_code
            return data
        except Exception as e:
            import traceback
            logger.error(f"[CHECKOUT_PLAIN_EXCEPTION] class={e.__class__.__name__} error={e}")
            logger.error(f"[CHECKOUT_PLAIN_TRACEBACK] {traceback.format_exc()}")
            return {"status": "error", "message": str(e), "_http_status": 500, "_traceback": traceback.format_exc()}

    async def checkout_best_available(self, slug: str, event_id: str, tickets: list, lang: str = "ar", payment_method: str = "credit_card", time_slot_id: str = None) -> dict:
        payload = self._checkout_order(
            event_id=event_id,
            tickets=tickets,
            lang=lang,
            payment_method=payment_method,
            extra={"time_slot_id": time_slot_id},
        )
        url = f"{self.BASE_URL}/event-detail/{slug}/checkout/hold-best-available"  # FIX: removed ?lang= — lang belongs only in the JSON body
        
        headers = self._build_headers(authenticated=True)
        final_headers = {**headers, "Authorization": f"Bearer {self.bearer_token}"}
        
        logger.info("=" * 80)
        logger.info("[CHECKOUT_BA_FULL_REQUEST] >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        logger.info(f"[CHECKOUT_BA_ENDPOINT] {url}")
        safe_headers = {k: v for k, v in final_headers.items() if k != 'Authorization' and k != 'User-Agent'}
        logger.info(f"[CHECKOUT_BA_HEADERS] {json.dumps(safe_headers, ensure_ascii=False)}")
        logger.info(f"[CHECKOUT_BA_PAYLOAD] {json.dumps(payload, ensure_ascii=False)}")
        logger.info("[CHECKOUT_BA_FULL_REQUEST] <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
        logger.info("=" * 80)
        
        try:
            resp = await self._request("POST", url, authenticated=True, json=payload)
            
            logger.info("=" * 80)
            logger.info("[CHECKOUT_BA_FULL_RESPONSE] >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
            logger.info(f"[CHECKOUT_BA_STATUS] {resp.status_code}")
            logger.info(f"[CHECKOUT_BA_RESPONSE_HEADERS] {dict(resp.headers)}")
            logger.info(f"[CHECKOUT_BA_RAW_BODY] {resp.text}")
            c_ids = {
                'x-request-id': resp.headers.get('x-request-id'),
                'x-correlation-id': resp.headers.get('x-correlation-id'),
                'trace-id': resp.headers.get('trace-id'),
            }
            logger.info(f"[CHECKOUT_BA_CORRELATION_IDS] {json.dumps(c_ids)}")
            logger.info("[CHECKOUT_BA_FULL_RESPONSE] <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
            logger.info("=" * 80)
            
            data = resp.json()
            if isinstance(data, dict):
                data["_http_status"] = resp.status_code
            return data
        except Exception as e:
            import traceback
            logger.error(f"[CHECKOUT_BA_EXCEPTION] class={e.__class__.__name__} error={e}")
            logger.error(f"[CHECKOUT_BA_TRACEBACK] {traceback.format_exc()}")
            return {"status": "error", "message": str(e), "_http_status": 500, "_traceback": traceback.format_exc()}

    async def checkout_seated(
        self, slug: str, seats: list, detail: dict = None,
        hold_token: str = None, event_id: str = None,
        lang: str = "ar", payment_method: str = "credit_card",
        time_slot_id: str = None, captcha_token: str = None,
        seats_io: dict = None, promo_code: str = None,
        operation_uuid: str = None,
        idempotency_key: str = None, # Corrected: Added separate key
    ) -> dict:
        """
        Event Seat Checkout - OFFICIAL API SPEC section 3.2
        POST /event-detail/{slug}/event-seat/checkout

        Required fields:
          selectedSeats*: [{ id*, label*, categoryKey* (number), chart: { holdToken } }]
          holdToken:      str - from /hold-token endpoint
          payment_method*: credit_card | apple_pay | stc_pay | mada
          lang*:          en | ar | fr
          redirect*:      str - success redirect URL
          redirect_failed*: str - failure redirect URL

        Optional fields:
          event_id:       str
          booking_source: str
          promo_code:     str
        """
        import json
        self._logger = __import__('logging').getLogger('webook')
        self._logger.info(
            f"[SEATED_CHECKOUT_PREP] slug={slug} event_id={event_id} "
            f"seats_count={len(seats) if seats else 0} hold_token_present={bool(hold_token)}"
        )

        # Format seats per spec 3.2
        seats_list = []
        for s in (seats or []):
            seat_obj = {
                "id": str(s.get("id", "")),
                "label": str(s.get("label", s.get("id", ""))),
                "categoryKey": int(s.get("categoryKey", s.get("category_key", 0))),
            }
            # Preserve General Admission fields if present
            if s.get("itemType") == "generalAdmission" or s.get("objectType") == "generalAdmission":
                seat_obj["itemType"] = s.get("itemType", "generalAdmission")
                seat_obj["objectType"] = s.get("objectType", "generalAdmission")
                if "numSelected" in s:
                    seat_obj["numSelected"] = int(s["numSelected"])
                if "amount" in s:
                    seat_obj["amount"] = int(s["amount"])
                if "selectedTicketType" in s:
                    seat_obj["selectedTicketType"] = s["selectedTicketType"]
                if "selectionPerTicketType" in s:
                    seat_obj["selectionPerTicketType"] = s["selectionPerTicketType"]
                if "name" in s:
                    seat_obj["name"] = s["name"]
                if "category" in s:
                    seat_obj["category"] = s["category"]

            if hold_token:
                seat_obj["chart"] = {"holdToken": hold_token}
            elif s.get("chart"):
                seat_obj["chart"] = s["chart"]
            seats_list.append(seat_obj)

        _EVENT_PAYMENT_METHODS = {"credit_card", "apple_pay", "stc_pay", "mada"}
        if payment_method not in _EVENT_PAYMENT_METHODS:
            payment_method = "credit_card"

        payload = {
            "selectedSeats": seats_list,
            "holdToken": hold_token or "",
            "payment_method": payment_method,
            "lang": lang,
            "redirect": f"https://webook.com/{lang}/payment-success",
            "redirect_failed": f"https://webook.com/{lang}/payment-failed",
        }

        if event_id:
            payload["event_id"] = event_id
        if promo_code:
            payload["promo_code"] = promo_code
        if captcha_token:
            payload["turnstile"] = captcha_token

        url = f"{self.BASE_URL}/event-detail/{slug}/event-seat/checkout"

        try:
            from core.logging.logger import logger
        except ImportError:
            logger = self._logger

        logger.info(f"[SEATED_CHECKOUT] POST {url}")
        logger.info(f"[SEATED_CHECKOUT] payload={json.dumps(payload, ensure_ascii=False, default=str)[:500]}")

        headers = {}
        if operation_uuid:
            headers["X-Operation-ID"] = operation_uuid
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        elif operation_uuid:
            headers["Idempotency-Key"] = operation_uuid

        try:
            resp = await self._request("POST", url, authenticated=True, json=payload, headers=headers)
            logger.info(f"[SEATED_CHECKOUT_RESP] status={resp.status_code} body={resp.text[:500]}")
            data = resp.json()
            if isinstance(data, dict):
                data["_http_status"] = resp.status_code
            return data
        except Exception as e:
            logger.error(f"[SEATED_CHECKOUT_ERR] {e.__class__.__name__}: {e}")
            return {"status": "error", "message": str(e), "_http_status": 500}

    async def release_reservation(self, slug: str, reservation_id: str = None, lang: str = "ar") -> dict:
        endpoint_patterns = [
            f"{self.BASE_URL}/event-detail/{slug}/hold/release",
            f"{self.BASE_URL}/reservations/hold/{reservation_id}",
            f"{self.BASE_URL}/event-detail/{slug}/release",
        ]
        for url in endpoint_patterns:
            try:
                logger.info(f"[API_FETCH] name=release_reservation method=POST url={url}")
                if reservation_id and "reservations/hold" in url:
                    resp = await self._request("DELETE", url, authenticated=True)
                else:
                    resp = await self._request(
                        "POST", url, authenticated=True,
                        json={"lang": lang, "reservation_id": reservation_id},
                    )
                logger.info(f"[API_RESPONSE] name=release_reservation status={resp.status_code} url={url}")
                if resp.status_code in (200, 204):
                    return {"status": "success", "_http_status": resp.status_code}
            except Exception as e:
                logger.warning(f"[RELEASE_RESERVATION] url={url} error={e}")
                continue
        logger.warning(f"[RELEASE_RESERVATION] slug={slug} all endpoints failed")
        return {"status": "error", "_http_status": 500}

    def _get_seatcloud_domain(self, workspace_key: str) -> str:
        """Detect if we should use seatcloud.com or seats.io."""
        if workspace_key and str(workspace_key).startswith("pk_"):
            return "seats.io"
        return "seatcloud.com"

    async def get_seatcloud_chart_data(self, workspace_key: str, chart_key: str) -> dict:
        domain = self._get_seatcloud_domain(workspace_key)
        url = f"https://api.{domain}/api/v2/{workspace_key}/map/{chart_key}/data?plain=true"
        logger.info(f"[SEATCLOUD_REQUEST] domain={domain} workspace_key={workspace_key} chart_key={chart_key} url={url}")
        try:
            logger.info(f"[API_FETCH] name=seatcloud_chart method=GET url={url}")
            resp = await self._request(
                "GET",
                url,
                headers={
                    "Accept": "application/json",
                    "Accept-Encoding": "identity",
                    "Origin": f"https://chart.{domain}",
                    "Referer": f"https://chart.{domain}/",
                },
            )
            raw = resp.content
            if raw[:2] == b"\x1f\x8b":
                import gzip as _gzip
                raw = _gzip.decompress(raw)
            logger.info(f"[API_RESPONSE] name=seatcloud_chart status={resp.status_code} bytes={len(raw)}")
            if resp.status_code != 200:
                logger.error(f"[SEATCLOUD_ERROR] status={resp.status_code} body={resp.text[:500]}")
                return {"_http_status": resp.status_code, "body": resp.text[:500]}
            data = json.loads(raw.decode("utf-8"))
            logger.info(f"[SEATCLOUD_RESPONSE] sections={len(data.get('sections', []))} chairs={len(data.get('content', {}).get('chairs', []))}")
            return data
        except Exception as e:
            logger.error(f"[API_EXCEPTION] name=seatcloud_chart class={e.__class__.__name__} error={e}")
            return {}

    async def get_seatcloud_report_available(self, workspace_key: str, event_key: str) -> list:
        """
        Fetch REAL-TIME availability report from SeatCloud.
        Authoritative source for high-competition sniping.
        """
        domain = self._get_seatcloud_domain(workspace_key)
        
        # Primary pattern: Singular 'event', no '/public', uses '/items' (Matches Browser)
        url = f"https://api.{domain}/api/v2/{workspace_key}/event/{event_key}/items"
        try:
            resp = await self._request(
                "GET", url,
                headers={
                    "Accept": "application/json",
                    "Origin": f"https://chart.{domain}",
                    "Referer": f"https://chart.{domain}/",
                }
            )
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, dict):
                    # /items often returns a dict with seat labels as keys
                    return list(data.values())
                if isinstance(data, list):
                    return data
                return []
            
            # Fallback pattern: Plural 'events', with '/public', uses 'reports/byStatus'
            url_alt = f"https://api.{domain}/api/v2/public/{workspace_key}/events/{event_key}/reports/byStatus?status=available"
            resp_alt = await self._request("GET", url_alt)
            if resp_alt.status_code == 200:
                data_alt = resp_alt.json()
                if isinstance(data_alt, dict):
                    return list(data_alt.values())
                if isinstance(data_alt, list):
                    return data_alt
                return []

            logger.warning(f"[SEATCLOUD_REPORT_FAIL] status={resp.status_code} url={url}")
            return []
        except Exception as e:
            logger.error(f"[SEATCLOUD_REPORT_EXCEPTION] {e}")
            return []


    async def hold_seat_via_websocket(
        self, workspace_key: str, chart_key: str, hold_token: str, seat_label: str, object_id: str = None
    ) -> bool:
        """Hold a seat in SeatCloud via public HTTP API (seats.io pattern), WS as fallback.
        Returns True if hold was registered successfully."""
        import base64 as _b64
        domain = self._get_seatcloud_domain(workspace_key)
        _auth = _b64.b64encode(f"{hold_token}:".encode()).decode()
        _hold_headers = {
            "Authorization": f"Basic {_auth}",
            "Content-Type": "application/json",
            "Origin": f"https://chart.{domain}",
            "Referer": f"https://chart.{domain}/",
        }
        # Try all known SeatCloud HTTP endpoint patterns
        # Try holding both object_id (UUID) and seat_label for maximum compatibility
        target_objects = list(set(filter(None, [object_id, seat_label])))
        _hold_body = {"objects": target_objects, "holdToken": hold_token}
        
        for endpoint in [
            f"https://api.{domain}/api/v2/public/events/{chart_key}/actions/hold",
            f"https://api.{domain}/api/v2/public/{workspace_key}/events/{chart_key}/actions/hold",
            f"https://api.{domain}/api/v2/{workspace_key}/event/{chart_key}/hold",
            f"https://api.{domain}/api/v2/{workspace_key}/events/{chart_key}/hold",
            f"https://api.{domain}/api/v2/{workspace_key}/event/{chart_key}/actions/hold",
        ]:
            try:
                resp = await self._request("POST", endpoint, json=_hold_body, headers=_hold_headers)
                logger.info(f"[SEATCLOUD_HTTP_HOLD] url={endpoint} status={resp.status_code} body={resp.text[:200]}")
                if resp.status_code in (200, 201, 204):
                    return True
            except Exception as e:
                logger.warning(f"[SEATCLOUD_HTTP_HOLD_FAIL] url={endpoint} error={e}")

        # FALLBACK: WebSocket hold — try every known format
        try:
            import websockets as _ws
            import asyncio as _asyncio
            import json as _json

            domain = self._get_seatcloud_domain(workspace_key)
            ws_url = (
                f"wss://api.{domain}:8443/"
                f"?event={chart_key}&token={hold_token}"
                f"&teamID={workspace_key}&channel=NO_CHANNEL"
            )
            logger.info(f"[SEATCLOUD_WS_CONNECT] url={ws_url} seat={seat_label}")
            async with _ws.connect(
                ws_url,
                additional_headers={
                    "Origin": f"https://chart.{domain}",
                    "Referer": f"https://chart.{domain}/",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
                },
                open_timeout=6,
                close_timeout=3,
            ) as ws:
                # Read any initial server messages (handshake / welcome frame)
                try:
                    init_raw = await _asyncio.wait_for(ws.recv(), timeout=1.5)
                    logger.info(f"[SEATCLOUD_WS_INIT] {str(init_raw)[:300]}")
                except _asyncio.TimeoutError:
                    pass

                # seats.io/SeatCloud WS formats — try all known variants
                # We try both the label and the internal object ID (if provided)
                target_ids = [seat_label]
                if object_id and object_id != seat_label:
                    target_ids.append(object_id)

                for tid in target_ids:
                    for msg_format in [
                        # seats.io v3 format (most likely)
                        {"type": "HOLD", "objectIds": [tid], "holdToken": hold_token},
                        # seats.io v2 format
                        {"type": "HOLD", "objects": [tid], "holdToken": hold_token},
                        # Capitalized Objects (requested by some SeatCloud versions)
                        {"type": "HOLD", "Objects": [tid], "holdToken": hold_token},
                        # pluralized and capitalized variants
                        {"type": "HOLD_OBJECTS", "Objects": [tid], "holdToken": hold_token},
                        {"type": "hold-objects", "objects": [tid], "holdToken": hold_token},
                        # action-based formats
                        {"action": "hold-object", "objects": [tid], "holdToken": hold_token},
                        {"action": "hold-objects", "objects": [tid], "holdToken": hold_token},
                        {"action": "hold", "objects": [tid], "holdToken": hold_token},
                        {"action": "hold", "Objects": [tid], "holdToken": hold_token},
                        # Nested data format (mirrors server→client broadcast structure)
                        {"action": "hold-object", "data": {"objects": [tid], "token": hold_token}},
                        {"action": "hold-objects", "data": {"objects": [tid], "token": hold_token}},
                        {"action": "hold", "data": {"Objects": [tid], "holdToken": hold_token}},
                        # Event-wrapped format
                        {"event": "hold", "data": {"objects": [tid], "holdToken": hold_token}},
                        {"event": "hold", "data": {"Objects": [tid], "holdToken": hold_token}},
                        {"event": "hold-objects", "data": {"Objects": [tid], "holdToken": hold_token}},
                    ]:
                        await ws.send(_json.dumps(msg_format))
                        logger.info(f"[SEATCLOUD_WS_SENT] id={tid} msg={_json.dumps(msg_format)}")
                        try:
                            raw = await _asyncio.wait_for(ws.recv(), timeout=1.5)
                            logger.info(f"[SEATCLOUD_WS_RECV] {str(raw)[:400]}")
                            try:
                                msg = _json.loads(raw)
                                err = msg.get("error")
                                if not err:
                                    logger.info(f"[SEATCLOUD_WS_HOLD_OK] id={tid} format={list(msg_format.keys())[:2]}")
                                    return True
                                # Log the actual action the server rejected so we can learn
                                logger.warning(f"[SEATCLOUD_WS_REJECTED] id={tid} sent_keys={list(msg_format.keys())} server_error={err}")
                            except Exception:
                                pass
                        except (_asyncio.TimeoutError, Exception):
                            pass
        except Exception as e:
            logger.error(f"[SEATCLOUD_WS_ERROR] {e}")
        return False

    async def get_held_items_seatcloud(
        self, workspace_key: str, chart_key: str, hold_token: str
    ) -> list:
        """GET /event/{chartKey}/items/held — returns [{uuid, label}, ...].
        The 'uuid' field is the allocation value Webook validates at checkout."""
        url = f"https://api.seatcloud.com/api/v2/{workspace_key}/event/{chart_key}/items/held"
        params = {"hold_token": hold_token, "plain": "true"}
        try:
            resp = await self._request("GET", url, params=params, headers={
                "Origin": "https://chart.seatcloud.com",
                "Referer": "https://chart.seatcloud.com/",
            })
            logger.info(
                f"[SEATCLOUD_HELD_RESPONSE] status={resp.status_code} body={resp.text[:400]}"
            )
            if resp.status_code == 200:
                data = resp.json()
                return data if isinstance(data, list) else []
            return []
        except Exception as e:
            logger.error(f"[SEATCLOUD_HELD_ERROR] {e}")
            return []

    async def hold_seats_seatcloud(self, workspace_key: str, chart_key: str, hold_token: str, seat_ids: list) -> dict:
        """Legacy stub — superseded by hold_seat_via_websocket + get_held_items_seatcloud."""
        logger.warning("[SEATCLOUD_HOLD_LEGACY] hold_seats_seatcloud called — prefer WS method")
        return {}

    async def get_resale_listing(self, slug: str = None, lang: str = "ar") -> list:
        """GET /tickets/resale-listing — view user resale listings (section 6.1)."""
        try:
            resp = await self._request("GET", f"{self.BASE_URL}/tickets/resale-listing", authenticated=True)
            return resp.json().get("data", []) if resp.status_code == 200 else []
        except Exception as e:
            logger.error(f"WebookClient: get_resale_listing failed: {e}")
            return []

    async def remove_resale_listing(self, listing_id: str) -> dict:
        """POST /tickets/remove-listing — remove a resale listing (section 6.2)."""
        payload = {"listing_id": listing_id}
        try:
            resp = await self._request("POST", f"{self.BASE_URL}/tickets/remove-listing",
                                       authenticated=True, json=payload)
            data = resp.json()
            if isinstance(data, dict):
                data["_http_status"] = resp.status_code
            return data
        except Exception as e:
            logger.error(f"WebookClient: remove_resale_listing failed: {e}")
            return {"success": False, "message": str(e), "_http_status": 500}

    # ── Ticket Management (sections 8.1–8.5) ────────────────────────────────

    async def send_tickets(
        self, order_id: str, tickets: list, email: str,
        first_name: str, last_name: str, send_with: str = "email",
        lang: str = "ar",
    ) -> dict:
        """POST /order/{order_id}/tickets/send-tickets (section 8.1)."""
        payload = {
            "tickets": tickets,        # [string] — list of ticket IDs
            "email": email,            # email*
            "first_name": first_name,  # first_name*
            "last_name": last_name,    # last_name*
            "send_with": send_with,    # send_with*
            "lang": lang,              # lang*
        }
        try:
            resp = await self._request(
                "POST", f"{self.BASE_URL}/order/{order_id}/tickets/send-tickets",
                authenticated=True, json=payload,
            )
            data = resp.json()
            if isinstance(data, dict):
                data["_http_status"] = resp.status_code
            return data
        except Exception as e:
            logger.error(f"WebookClient: send_tickets failed: {e}")
            return {"success": False, "message": str(e), "_http_status": 500}

    async def accept_tickets(
        self, order_id: str, tickets: list, transaction_id: str, lang: str = "ar",
    ) -> dict:
        """POST /order/{order_id}/tickets/accept-tickets (section 8.2)."""
        payload = {
            "tickets": tickets,               # [string]*
            "lang": lang,                     # lang*
            "transaction_id": transaction_id, # transaction_id*
        }
        try:
            resp = await self._request(
                "POST", f"{self.BASE_URL}/order/{order_id}/tickets/accept-tickets",
                authenticated=True, json=payload,
            )
            data = resp.json()
            if isinstance(data, dict):
                data["_http_status"] = resp.status_code
            return data
        except Exception as e:
            logger.error(f"WebookClient: accept_tickets failed: {e}")
            return {"success": False, "message": str(e), "_http_status": 500}

    async def reject_tickets(
        self, order_id: str, tickets: list, transaction_id: str, lang: str = "ar",
    ) -> dict:
        """POST /order/{order_id}/tickets/reject-tickets (section 8.3)."""
        payload = {
            "tickets": tickets,
            "lang": lang,
            "transaction_id": transaction_id,
        }
        try:
            resp = await self._request(
                "POST", f"{self.BASE_URL}/order/{order_id}/tickets/reject-tickets",
                authenticated=True, json=payload,
            )
            data = resp.json()
            if isinstance(data, dict):
                data["_http_status"] = resp.status_code
            return data
        except Exception as e:
            logger.error(f"WebookClient: reject_tickets failed: {e}")
            return {"success": False, "message": str(e), "_http_status": 500}

    async def cancel_tickets(
        self, order_id: str, tickets: list, transaction_id: str, lang: str = "ar",
    ) -> dict:
        """POST /order/{order_id}/tickets/cancel-tickets (section 8.4)."""
        payload = {
            "tickets": tickets,
            "lang": lang,
            "transaction_id": transaction_id,
        }
        try:
            resp = await self._request(
                "POST", f"{self.BASE_URL}/order/{order_id}/tickets/cancel-tickets",
                authenticated=True, json=payload,
            )
            data = resp.json()
            if isinstance(data, dict):
                data["_http_status"] = resp.status_code
            return data
        except Exception as e:
            logger.error(f"WebookClient: cancel_tickets failed: {e}")
            return {"success": False, "message": str(e), "_http_status": 500}

    async def get_pending_transfers(self) -> dict:
        """GET /user/pending-transfers (section 8.5)."""
        try:
            resp = await self._request(
                "GET", f"{self.BASE_URL}/user/pending-transfers", authenticated=True
            )
            data = resp.json()
            if isinstance(data, dict):
                data["_http_status"] = resp.status_code
            return data
        except Exception as e:
            logger.error(f"WebookClient: get_pending_transfers failed: {e}")
            return {"success": False, "message": str(e), "_http_status": 500}

    # ── User Bookings (sections 9.1–9.4) ─────────────────────────────────────

    async def get_user_booking_detail(self, order_id: str, lang: str = "ar") -> dict:
        """GET /user/bookings/{orderId} (section 9.2)."""
        try:
            resp = await self._request(
                "GET", f"{self.BASE_URL}/user/bookings/{order_id}",
                params={"lang": lang}, authenticated=True,
            )
            data = resp.json()
            if isinstance(data, dict):
                data["_http_status"] = resp.status_code
            return data
        except Exception as e:
            logger.error(f"WebookClient: get_user_booking_detail failed: {e}")
            return {"_http_status": 500, "message": str(e)}

    async def get_user_bookings_season(
        self, lang: str = "ar", page: int = 1, per_page: int = 20
    ) -> dict:
        """GET /user/bookings-season (section 9.3)."""
        params = {"lang": lang, "page": str(page), "per_page": str(per_page)}
        try:
            resp = await self._request(
                "GET", f"{self.BASE_URL}/user/bookings-season",
                params=params, authenticated=True,
            )
            return resp.json() if resp.status_code == 200 else {}
        except Exception as e:
            logger.error(f"WebookClient: get_user_bookings_season failed: {e}")
            return {}

    async def get_user_booking_season_detail(self, order_id: str, lang: str = "ar") -> dict:
        """GET /user/bookings-season/{order_id} (section 9.4)."""
        try:
            resp = await self._request(
                "GET", f"{self.BASE_URL}/user/bookings-season/{order_id}",
                params={"lang": lang}, authenticated=True,
            )
            data = resp.json()
            if isinstance(data, dict):
                data["_http_status"] = resp.status_code
            return data
        except Exception as e:
            logger.error(f"WebookClient: get_user_booking_season_detail failed: {e}")
            return {"_http_status": 500, "message": str(e)}

    # ── User Profile (sections 10.1–10.2) ────────────────────────────────────

    async def update_profile(
        self, first_name: str, last_name: str, phone: str = None,
        country_code: str = None, nationality: str = None, country: str = None,
        skip_phone_validation: bool = False,
    ) -> dict:
        """POST /update-profile (section 10.1)."""
        payload: dict = {
            "first_name": first_name,  # first_name*
            "last_name": last_name,    # last_name*
            "skip_phone_validation": skip_phone_validation,
        }
        if phone:
            payload["phone"] = phone
        if country_code:
            payload["country_code"] = country_code
        if nationality:
            payload["nationality"] = nationality
        if country:
            payload["country"] = country
        try:
            resp = await self._request(
                "POST", f"{self.BASE_URL}/update-profile",
                authenticated=True, json=payload,
            )
            data = resp.json()
            if isinstance(data, dict):
                data["_http_status"] = resp.status_code
            return data
        except Exception as e:
            logger.error(f"WebookClient: update_profile failed: {e}")
            return {"success": False, "message": str(e), "_http_status": 500}

    async def update_favorite_team(self, team_id: str) -> dict:
        """POST /update-favorite-team (section 7.2)."""
        try:
            resp = await self._request(
                "POST", f"{self.BASE_URL}/update-favorite-team",
                authenticated=True, json={"team_id": team_id},
            )
            data = resp.json()
            if isinstance(data, dict):
                data["_http_status"] = resp.status_code
            return data
        except Exception as e:
            logger.error(f"WebookClient: update_favorite_team failed: {e}")
            return {"success": False, "message": str(e), "_http_status": 500}

    async def get_teams_list(self, lang: str = "ar") -> dict:
        """GET /teams/list (section 7.1)."""
        try:
            resp = await self._request(
                "GET", f"{self.BASE_URL}/teams/list",
                params={"lang": lang}, authenticated=True,
            )
            data = resp.json()
            if isinstance(data, dict):
                data["_http_status"] = resp.status_code
            return data
        except Exception as e:
            logger.error(f"WebookClient: get_teams_list failed: {e}")
            return {}

    async def check_blacklist(self, slug: str, lang: str = "ar") -> dict:
        params = {"lang": lang, "event_slug": slug}
        try:
            resp = await self._request("GET", f"{self.BASE_URL}/blacklists/check", params=params, authenticated=True)
            if resp.status_code == 200:
                return resp.json().get("data", resp.json())
            return {"is_blacklisted": False, "_http_status": resp.status_code}
        except Exception as e:
            logger.error(f"WebookClient: check_blacklist failed: {e}")
            return {"is_blacklisted": False, "error": str(e)}
