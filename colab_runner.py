#!/usr/bin/env python3
"""
colab_runner.py - Webook Platform & Telegram Sniper Colab Launcher
Designed specifically for Google Colab and remote headless environments.
Orchestrates:
  1. Cloudflare / Localtunnel external tunnels (for Port 8501 Streamlit & Port 8000 FastAPI)
  2. Public IP resolution (for Localtunnel authentication password)
  3. Concurrent execution of FastAPI + Streamlit + Telegram Bot + Sniper Engines
"""
import os
import sys
import json
import time
import shutil
import asyncio
import subprocess
import urllib.request
import re
from pathlib import Path
from typing import Optional

# Setup Root Directory
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def get_colab_public_ip() -> str:
    """Fetches the external public IP of the Google Colab VM (Used as the Localtunnel password)."""
    try:
        req = urllib.request.Request("https://ipv4.icanhazip.com", headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=4) as resp:
            return resp.read().decode("utf-8").strip()
    except Exception:
        return "Not available (Run 'curl ifconfig.me' in cell)"

def get_cf_binary() -> Optional[str]:
    """Finds available cloudflared executable."""
    candidate = shutil.which("cloudflared")
    if candidate:
        return candidate
    for p in ["/usr/local/bin/cloudflared", "/tmp/cloudflared", "/usr/bin/cloudflared"]:
        if os.path.exists(p) and os.access(p, os.X_OK):
            return p
    return None

def ensure_cloudflared() -> bool:
    """Downloads and setups cloudflared binary on Linux/Colab for zero-password instant tunnels."""
    if get_cf_binary():
        return True
    try:
        print("[SETUP] Installing Cloudflared for instant, password-free tunnel...")
        cmd = "curl -L --silent https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /tmp/cloudflared && chmod +x /tmp/cloudflared"
        subprocess.run(cmd, shell=True, check=True)
        return bool(get_cf_binary())
    except Exception as e:
        print(f"[SETUP] Could not install cloudflared ({e}), falling back to localtunnel.")
        return False

def extract_cf_tunnel_url(log_text: str) -> Optional[str]:
    """Strictly extracts the assigned quick tunnel subdomain URL (e.g. https://xxx-yyy.trycloudflare.com)."""
    matches = re.findall(r'https://([a-zA-Z0-9\-]+)\.trycloudflare\.com', log_text, re.IGNORECASE)
    for sub in matches:
        sub_clean = sub.strip().lower()
        if sub_clean and sub_clean not in ["www", "api", "trycloudflare", "blog", "docs", "static"]:
            return f"https://{sub}.trycloudflare.com"
    return None

def start_cloudflare_tunnel(port: int, service_name: str = "Streamlit") -> Optional[str]:
    """Starts a Cloudflare quick tunnel targeting the given port and captures the unique trycloudflare.com URL."""
    cf_bin = get_cf_binary()
    if not cf_bin:
        return None
    try:
        log_file = PROJECT_ROOT / f".cf_{service_name.lower()}.log"
        f = open(log_file, "w")
        cmd = [cf_bin, "tunnel", "--url", f"http://127.0.0.1:{port}"]
        proc = subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT)
        
        # Wait up to 25 seconds for the actual assigned quick tunnel URL
        for _ in range(50):
            time.sleep(0.5)
            if log_file.exists():
                text = log_file.read_text(encoding="utf-8", errors="ignore")
                url = extract_cf_tunnel_url(text)
                if url:
                    return url
        return None
    except Exception as e:
        print(f"[TUNNEL_WARN] Cloudflare tunnel failed for {service_name}: {e}")
        return None

def start_localtunnel_fallback(port: int, subdomain: Optional[str] = None) -> Optional[str]:
    """Fallback to npx localtunnel if cloudflared is unavailable."""
    try:
        log_file = PROJECT_ROOT / f".lt_{port}.log"
        f = open(log_file, "w")
        cmd = ["npx", "localtunnel", "--port", str(port)]
        if subdomain:
            cmd.extend(["--subdomain", subdomain])
        proc = subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT)
        
        for _ in range(30):
            time.sleep(0.5)
            if log_file.exists():
                text = log_file.read_text(encoding="utf-8", errors="ignore")
                matches = re.findall(r'https?://[a-zA-Z0-9\-]+\.loca\.lt', text)
                if matches:
                    return matches[0]
                for line in text.splitlines():
                    if "loca.lt" in line and "your url is:" in line.lower():
                        parts = line.split("is:")
                        if len(parts) > 1:
                            return parts[1].strip()
        return None
    except Exception as e:
        print(f"[TUNNEL_WARN] Localtunnel failed for port {port}: {e}")
        return None

def print_colab_banner(unified_url: str, colab_ip: str):
    print("\n" + "═" * 78)
    print("🎯 WEBOOK INGESTION & ULTRA SNIPER PLATFORM - WEB DASHBOARD PORTAL")
    print("═" * 78)
    print("🌐 رابط صفحة الويب الموحدة والشاملة للمنظومة (تفتح في المتصفح مباشرة):")
    print(f"   👉 {unified_url}")
    print()
    print("📌 ماذا تجد في صفحة الويب الشاملة بنقرة واحدة وبدون أي بوت خارجي؟")
    print(f"   1. 🎯 لوحة القنص السريع وتجاوز طابور الانتظار وحجز المقاعد: {unified_url}/")
    print(f"   2. 🎟️ مستكشف فعاليات Webook.com والمقاعد والأسعار المباشرة")
    print(f"   3. 👥 إدارة حسابات Webook وجلسات Cloudflare والحجز التلقائي")
    print(f"   4. 📊 السجل اللحظي المباشر ومؤشرات سرعة الاستجابة (14ms)")
    print(f"   5. ⚙️  خادم واجهة التطبيقات المباشر: {unified_url}/api")
    print(f"   6. 📚 توثيق الـ API التفاعلي المفتوح: {unified_url}/docs")
    print()
    if "loca.lt" in unified_url:
        print("🔑 كلمة مرور Localtunnel (إذا طلبها الموقع في أول زيارة):")
        print(f"   👉 {colab_ip}")
        print("   (انسخ هذا الرقم والصقه في مربع 'Tunnel Password' واضغط Submit)")
        print()
    print("💡 لا حاجة لأي تطبيق خارجي — كل العمليات تتم وتُدار داخل صفحة الويب مباشرة!")
    print("═" * 78 + "\n")

def main():
    print("[INIT] Starting Webook Colab Environment Initializer...")
    
    # 1. Setup IP and Single Unified Tunnel
    colab_ip = get_colab_public_ip()
    ensure_cloudflared()
    
    print("[1/4] Creating External Unified Public Tunnel (Single Link for All Services)...")
    # Single Unified Tunnel on Port 8000 (Serves Web GUI at /, REST API at /api, Docs at /docs)
    unified_url = start_cloudflare_tunnel(8000, "Webook_Portal")
    if not unified_url or unified_url.rstrip("/").lower() in ["https://trycloudflare.com", "http://trycloudflare.com"]:
        print("[TUNNEL] Cloudflare assigned url invalid or unavailable, trying localtunnel fallback...")
        unified_url = start_localtunnel_fallback(8000)
    if not unified_url:
        unified_url = "http://localhost:8000"

    # Store tunnel urls in environment for python apps to consume
    os.environ["PUBLIC_UNIFIED_URL"] = unified_url
    os.environ["PUBLIC_STREAMLIT_URL"] = unified_url
    os.environ["PUBLIC_API_URL"] = f"{unified_url}/api"
    
    # Save to .tunnel_info.json
    try:
        with open(PROJECT_ROOT / ".tunnel_info.json", "w", encoding="utf-8") as tf:
            json.dump({
                "unified_url": unified_url,
                "streamlit": unified_url,
                "api": f"{unified_url}/api",
                "lan_ip": colab_ip,
                "updated_at": time.time()
            }, tf, indent=2)
    except Exception:
        pass

    print_colab_banner(unified_url, colab_ip)

    # 2. Launch Streamlit UI Subprocess
    print("[2/4] Starting Streamlit GUI Process...")
    st_app_path = PROJECT_ROOT / "apps" / "ui" / "app.py"
    if not st_app_path.exists():
        st_app_path = PROJECT_ROOT / "main.py"

    st_env = os.environ.copy()
    st_env["PYTHONPATH"] = str(PROJECT_ROOT)
    st_cmd = [
        sys.executable, "-m", "streamlit", "run", str(st_app_path),
        "--server.port=8501",
        "--server.address=0.0.0.0",
        "--server.headless=true",
        "--server.enableCORS=false",
        "--server.enableXsrfProtection=false",
        "--browser.gatherUsageStats=false"
    ]
    st_proc = subprocess.Popen(st_cmd, env=st_env)

    # 3. Import and Run FastAPI Backend & Web Portal
    print("[3/4] Initializing FastAPI Backend & Web Services...")
    try:
        import uvicorn
        from apps.api.main import app as api_app
        config = uvicorn.Config(
            api_app,
            host="0.0.0.0",
            port=8000,
            log_level="info",
            access_log=False
        )
        server = uvicorn.Server(config)
        asyncio.run(server.serve())
    except KeyboardInterrupt:
        print("\n[STOP] Shutting down Webook Colab Services...")
    finally:
        if st_proc and st_proc.poll() is None:
            st_proc.terminate()

if __name__ == "__main__":
    main()
