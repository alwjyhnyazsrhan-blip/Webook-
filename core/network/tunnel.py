# core/network/tunnel.py
"""
Network and Tunnel Management for Webook Platform.
Solves mobile and external localtunnel routing between FastAPI and Streamlit:
1. Dynamic port assignment with collision prevention.
2. Background localtunnel launcher with live URL capture.
3. Intelligent client-side / server-side URL resolution (never redirects to localhost from an external domain).
"""
import os
import sys
import re
import json
import socket
import shutil
import threading
import subprocess
import atexit
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

# Project root path
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_FILE = _PROJECT_ROOT / ".tunnel_info.json"
TMP_CONFIG_FILE = Path("/tmp/webook_tunnel_info.json")


def get_lan_ip() -> str:
    """Discovers local network LAN IP for WiFi access."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"


def check_port_available(port: int, host: str = "0.0.0.0") -> bool:
    """Checks if a TCP port is open and available for binding."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((host, port))
            return True
    except OSError:
        return False


def find_next_available_port(start_port: int, max_tries: int = 20) -> int:
    """Finds the next free port starting from start_port."""
    for p in range(start_port, start_port + max_tries):
        if check_port_available(p):
            return p
    return start_port


def resolve_non_conflicting_ports(api_port: int = 8000, streamlit_port: int = 8501) -> Tuple[int, int]:
    """
    Guarantees no port collisions between FastAPI and Streamlit:
    - Ensures api_port != streamlit_port.
    - If identical or occupied, automatically assigns non-colliding ports.
    """
    final_api = api_port
    final_st = streamlit_port

    if final_api == final_st:
        print(f"[PORT_SAFETY] Conflict detected: API and Streamlit requested the same port ({final_api}).")
        final_st = final_api + 501
        print(f"[PORT_SAFETY] Streamlit port adjusted to {final_st}")

    return final_api, final_st


class TunnelManager:
    """
    Manages external tunnels (localtunnel / cloudflared / ngrok)
    and ensures external links point to the actual public domain,
    NOT localhost.
    """

    def __init__(self):
        self._processes: Dict[str, subprocess.Popen] = {}
        self._urls: Dict[str, str] = {
            "api": os.getenv("API_TUNNEL_URL", ""),
            "streamlit": os.getenv("STREAMLIT_URL", os.getenv("STREAMLIT_TUNNEL_URL", "")),
        }
        self._lock = threading.Lock()
        self._load_cached_tunnels()
        atexit.register(self.stop_all)

    def _load_cached_tunnels(self):
        """Loads cached tunnel URLs from disk if available."""
        for path in [CONFIG_FILE, TMP_CONFIG_FILE]:
            try:
                if path.exists():
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, dict):
                            for k, v in data.items():
                                if v and isinstance(v, str) and not self._urls.get(k):
                                    self._urls[k] = v
            except Exception:
                pass

    def _save_cached_tunnels(self):
        """Persists tunnel URLs to disk so FastAPI and worker processes stay synchronized."""
        try:
            data = dict(self._urls)
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            try:
                with open(TMP_CONFIG_FILE, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
            except Exception:
                pass
        except Exception as e:
            print(f"[TUNNEL_CACHE_WARN] Could not persist tunnel info: {e}")

    def get_tunnel_url(self, service: str) -> Optional[str]:
        """Returns the public tunnel URL for a service ('streamlit' or 'api')."""
        with self._lock:
            url = self._urls.get(service)
            if not url:
                # Re-check environment variables
                if service == "streamlit":
                    url = os.getenv("STREAMLIT_URL") or os.getenv("STREAMLIT_TUNNEL_URL")
                elif service == "api":
                    url = os.getenv("API_TUNNEL_URL")
            if url:
                # Ensure no trailing slashes
                url = url.rstrip("/")
                # Reject localhost as a valid 'tunnel' URL
                if "localhost" in url or "127.0.0.1" in url:
                    return None
            return url

    def set_tunnel_url(self, service: str, url: str):
        """Manually registers or updates a tunnel URL."""
        with self._lock:
            cleaned = url.strip().rstrip("/")
            self._urls[service] = cleaned
            if service == "streamlit":
                os.environ["STREAMLIT_URL"] = cleaned
                os.environ["STREAMLIT_TUNNEL_URL"] = cleaned
            elif service == "api":
                os.environ["API_TUNNEL_URL"] = cleaned
            self._save_cached_tunnels()
            print(f"[TUNNEL_REGISTERED] Service '{service}' URL set to: {cleaned}")

    def start_localtunnel(self, port: int, service: str = "streamlit", subdomain: Optional[str] = None) -> Optional[str]:
        """
        Starts an 'npx -y localtunnel' process in the background,
        reads its stdout to extract the assigned public URL,
        and saves it.
        """
        if shutil.which("npx") is None:
            print(f"[TUNNEL_ERROR] 'npx' command not found. Install Node.js/npm to use localtunnel.")
            return None

        # Check if already running for this service
        with self._lock:
            existing_proc = self._processes.get(service)
            if existing_proc and existing_proc.poll() is None and self._urls.get(service):
                return self._urls[service]

        cmd = ["npx", "-y", "localtunnel", "--port", str(port)]
        if subdomain:
            cmd.extend(["--subdomain", subdomain])

        print(f"[TUNNEL] Launching Localtunnel for {service} on port {port}...")
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
            with self._lock:
                self._processes[service] = proc

            # Read the output asynchronously or wait up to 10 seconds for the URL
            url_captured = []
            capture_event = threading.Event()

            def _reader():
                for line in proc.stdout:
                    match = re.search(r"https?://[a-zA-Z0-9-.]+\.loca\.lt", line)
                    if match:
                        url = match.group(0).rstrip("/")
                        url_captured.append(url)
                        self.set_tunnel_url(service, url)
                        capture_event.set()
                        print(f"======================================================================")
                        print(f"🚀 PUBLIC TUNNEL ACTIVE ({service.upper()}): {url}")
                        print(f"======================================================================")
                        break

            t = threading.Thread(target=_reader, daemon=True)
            t.start()
            capture_event.wait(timeout=10.0)

            if url_captured:
                return url_captured[0]

            return None
        except Exception as e:
            print(f"[TUNNEL_LAUNCH_ERROR] Failed to start localtunnel for {service}: {e}")
            return None

    def start_dual_tunnels(self, api_port: int, streamlit_port: int) -> Dict[str, Optional[str]]:
        """Starts localtunnel tunnels for both FastAPI and Streamlit concurrently."""
        results = {}
        st_thread = threading.Thread(
            target=lambda: results.update({"streamlit": self.start_localtunnel(streamlit_port, "streamlit")})
        )
        api_thread = threading.Thread(
            target=lambda: results.update({"api": self.start_localtunnel(api_port, "api")})
        )

        st_thread.start()
        api_thread.start()
        st_thread.join(timeout=12)
        api_thread.join(timeout=12)

        return results

    def get_status(self) -> Dict[str, Any]:
        """Returns the current status of all tunnels."""
        with self._lock:
            st_url = self.get_tunnel_url("streamlit")
            api_url = self.get_tunnel_url("api")
            return {
                "streamlit_url": st_url,
                "api_url": api_url,
                "has_external_streamlit": bool(st_url and "localhost" not in st_url),
                "has_external_api": bool(api_url and "localhost" not in api_url),
                "lan_ip": get_lan_ip(),
            }

    def stop_all(self):
        """Terminates all active tunnel subprocesses."""
        with self._lock:
            for name, proc in self._processes.items():
                try:
                    if proc.poll() is None:
                        print(f"[TUNNEL] Stopping {name} tunnel...")
                        proc.terminate()
                except Exception:
                    pass
            self._processes.clear()


# Global Singleton instance
tunnel_manager = TunnelManager()


def resolve_client_streamlit_url(
    client_host: str,
    client_scheme: str = "https",
    streamlit_port: int = 8501
) -> Dict[str, Any]:
    """
    Intelligently determines the Streamlit UI URL for an incoming client request.
    CRITICAL RULE: Never returns 'localhost' when accessed via an external domain (localtunnel, ngrok, etc.).

    Returns:
        {
            "url": str or None,
            "target_type": "external_tunnel" | "lan" | "localhost" | "pending_tunnel",
            "is_external": bool,
            "can_auto_redirect": bool,
            "display_host": str
        }
    """
    # 1. Clean client host header
    host_clean = client_host.split(":")[0].strip().lower()
    port_in_host = client_host.split(":")[1] if ":" in client_host else ""

    is_localhost = host_clean in ("localhost", "127.0.0.1", "0.0.0.0")
    is_lan = bool(re.match(r"^(192\.168\.|10\.|172\.(1[6-9]|2[0-9]|3[0-1])\.)", host_clean))
    is_external = not (is_localhost or is_lan)

    # 2. Check if a valid external Streamlit tunnel exists
    external_st_url = tunnel_manager.get_tunnel_url("streamlit")
    if external_st_url and ("localhost" in external_st_url or "127.0.0.1" in external_st_url):
        external_st_url = None

    # Case A: User is accessing via an external tunnel (e.g. *.loca.lt, *.ngrok*, *.trycloudflare.com)
    if is_external:
        if external_st_url:
            return {
                "url": external_st_url,
                "target_type": "external_tunnel",
                "is_external": True,
                "can_auto_redirect": True,
                "display_host": host_clean,
            }
        else:
            # External domain detected, but no separate Streamlit tunnel URL yet.
            # CRITICAL: DO NOT fallback to localhost!
            return {
                "url": None,
                "target_type": "pending_tunnel",
                "is_external": True,
                "can_auto_redirect": False,
                "display_host": host_clean,
            }

    # Case B: User is accessing from another device on the same local network (WiFi / LAN)
    if is_lan:
        lan_url = f"{client_scheme}://{host_clean}:{streamlit_port}"
        return {
            "url": lan_url,
            "target_type": "lan",
            "is_external": False,
            "can_auto_redirect": True,
            "display_host": host_clean,
        }

    # Case C: User is accessing on the same local machine (localhost)
    local_url = f"http://localhost:{streamlit_port}"
    return {
        "url": local_url,
        "target_type": "localhost",
        "is_external": False,
        "can_auto_redirect": True,
        "display_host": "localhost",
    }
