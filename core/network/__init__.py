# core/network/__init__.py
"""
Network and Tunnel Management for Webook Platform
Handles dynamic port collision prevention, localtunnel orchestration,
and mobile-friendly external routing between FastAPI and Streamlit.
"""
from .tunnel import (
    TunnelManager,
    tunnel_manager,
    check_port_available,
    resolve_non_conflicting_ports,
    resolve_client_streamlit_url,
    get_lan_ip,
)

__all__ = [
    "TunnelManager",
    "tunnel_manager",
    "check_port_available",
    "resolve_non_conflicting_ports",
    "resolve_client_streamlit_url",
    "get_lan_ip",
]
