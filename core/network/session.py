import httpx
from typing import Optional, Dict
from core.logging.logger import logger

class NetworkManager:
    """
    PHASE 3: Production HTTP Lifecycle Management.
    Provides isolated sessions per account to prevent cookie contamination.
    """
    _clients: Dict[str, httpx.AsyncClient] = {}

    @classmethod
    async def get_client(cls, session_id: str = "default", proxy: str = None, force_new: bool = False, initial_cookies: dict = None) -> httpx.AsyncClient:
        """
        Returns an isolated AsyncClient for the given session_id.
        initial_cookies: Optional dict of cookies to seed the new client.
        """
        if force_new and session_id in cls._clients:
            client = cls._clients.pop(session_id)
            if not client.is_closed:
                await client.aclose()
            logger.info(f"NetworkManager: Force-closed client for session '{session_id}' (Clearing Runtime Cookies)")

        if session_id not in cls._clients or cls._clients[session_id].is_closed:
            limits = httpx.Limits(max_connections=20, max_keepalive_connections=5, keepalive_expiry=30.0)
            timeout = httpx.Timeout(15.0, connect=5.0)
            proxies = {"http://": proxy, "https://": proxy} if proxy else None
            
            jar = httpx.Cookies()
            if initial_cookies:
                for k, v in initial_cookies.items():
                    jar.set(k, v)
            
            cls._clients[session_id] = httpx.AsyncClient(
                limits=limits,
                timeout=timeout,
                proxies=proxies,
                http2=True,
                follow_redirects=True,
                cookies=jar
            )
            logger.info(f"NetworkManager: Isolated AsyncClient created for session '{session_id}' | cookies_seeded={initial_cookies is not None}")
            
        return cls._clients[session_id]

    @classmethod
    def get_cookies(cls, session_id: str) -> dict:
        if session_id in cls._clients:
            return dict(cls._clients[session_id].cookies)
        return {}


    @classmethod
    async def close_all(cls):
        for session_id, client in cls._clients.items():
            if not client.is_closed:
                await client.aclose()
        cls._clients.clear()
        logger.info("NetworkManager: All isolated clients closed")

network_manager = NetworkManager()
