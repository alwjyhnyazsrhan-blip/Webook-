
import asyncio
from modules.webook.client import WebookApiClient
from core.network.session import network_manager

async def audit_internal_proxies():
    test_configs = [
        {"id": "acc_alpha", "proxy": "http://user:pass@proxy-alpha:8080"},
        {"id": "acc_beta", "proxy": "http://user:pass@proxy-beta:8080"},
        {"id": "acc_none", "proxy": None},
    ]
    
    print("--- INTERNAL NETWORK AUDIT (Proxy Affinity) ---")
    
    for cfg in test_configs:
        # 1. Initialize client
        client = WebookApiClient(account_id=cfg["id"], proxy=cfg["proxy"])
        
        # 2. Trigger session creation
        # We don't actually need to send a reuest, just get the client
        from core.network.session import network_manager
        httpx_client = await network_manager.get_client(session_id=cfg["id"], proxy=cfg["proxy"])
        
        # 3. Inspect Mounts (where httpx stores proxies)
        # In httpx, proxies are stored in _mounts
        # Keys are BaseURL patterns like 'all://' or 'https://'
        mounts = getattr(httpx_client, "_mounts", {})
        proxy_found = "NONE"
        for pattern, m in mounts.items():
            if hasattr(m, "_proxy_url"):
                proxy_found = str(getattr(m, "_proxy_url"))
        
        print(f"Session: {cfg['id']:<10} | Target Proxy: {str(cfg['proxy']):<30} | Actual Mount: {proxy_found}")

    await network_manager.close_all()

if __name__ == "__main__":
    asyncio.run(audit_internal_proxies())
