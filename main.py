# ==============================================================================
# Webook Ingestion & Sniper Control Platform - Main Entrypoint
# Standardized Clean Absolute Imports & Robust Multi-Environment Compatibility
# ==============================================================================
import os
import sys
import argparse
import subprocess
import asyncio
import threading
import time
from pathlib import Path

# ------------------------------------------------------------------------------
# 1. Deterministic Project Root & Python Path Configuration
# ------------------------------------------------------------------------------
# Resolve the true project root (the directory containing this main.py)
PROJECT_ROOT = Path(__file__).resolve().parent

# Ensure the project root is explicitly at the head of sys.path
root_str = str(PROJECT_ROOT)
if root_str in sys.path:
    sys.path.remove(root_str)
sys.path.insert(0, root_str)

# Ensure PYTHONPATH environment variable reflects the project root for child processes
current_pythonpath = os.environ.get("PYTHONPATH", "")
if root_str not in current_pythonpath.split(os.pathsep):
    os.environ["PYTHONPATH"] = f"{root_str}{os.pathsep}{current_pythonpath}" if current_pythonpath else root_str

# Install or verify .pth file in python user/system site-packages if writable (failsafe)
try:
    import site
    site_dirs = site.getsitepackages() if hasattr(site, "getsitepackages") else []
    user_site = site.getusersitepackages() if hasattr(site, "getusersitepackages") else None
    if user_site:
        site_dirs.append(user_site)
    for sdir in site_dirs:
        try:
            pth_path = Path(sdir) / "webook.pth"
            if not pth_path.exists():
                pth_path.parent.mkdir(parents=True, exist_ok=True)
                pth_path.write_text(f"{root_str}\n", encoding="utf-8")
                break
        except Exception:
            continue
except Exception:
    pass

# ------------------------------------------------------------------------------
# 2. Clean Absolute Imports for All Modules
# ------------------------------------------------------------------------------
# Core Platform Configuration & Logging
from core.config.settings import settings
from core.logging.logger import logger

# Core Database & Models
from database.models import Base
from core.database.postgres import engine, AsyncSessionLocal

# Core Services
from services.discovery.engine import DiscoveryEngine
from services.reservation.swapper import HoldSwapper
from services.monitor.ghost import GhostMonitor

# Core Network & Dynamic Tunnel Management
from core.network.tunnel import (
    tunnel_manager,
    resolve_non_conflicting_ports,
    check_port_available,
    get_lan_ip,
)

# API Application (FastAPI Decoupled Backend)
try:
    from apps.api.main import app as api_app
except Exception as e:
    logger.warning(f"[API_IMPORT_FALLBACK] {e}")
    from fastapi import FastAPI
    api_app = FastAPI(title="Webook Platform API Fallback")

# Bot Application
try:
    from apps.bot.main import start_bot
except Exception as e:
    logger.warning(f"[BOT_IMPORT_FALLBACK] {e}")
    async def start_bot():
        logger.info("[BOT] Bot stub active.")

# ------------------------------------------------------------------------------
# 3. Port & Host Safety Configuration
# ------------------------------------------------------------------------------
_RAW_API_PORT = int(os.getenv("API_PORT", str(getattr(settings, "api_port", 8000))))
_RAW_STREAMLIT_PORT = int(os.getenv("STREAMLIT_PORT", "8501"))
API_PORT, STREAMLIT_PORT = resolve_non_conflicting_ports(_RAW_API_PORT, _RAW_STREAMLIT_PORT)
API_HOST = os.getenv("API_HOST", getattr(settings, "api_host", "0.0.0.0"))
STREAMLIT_HOST = os.getenv("STREAMLIT_HOST", "0.0.0.0")

os.environ["API_PORT"] = str(API_PORT)
os.environ["STREAMLIT_PORT"] = str(STREAMLIT_PORT)

discovery_engine = DiscoveryEngine()

# ------------------------------------------------------------------------------
# 4. Background Service Loops
# ------------------------------------------------------------------------------
async def background_sync_loop():
    """PHASE 5: LIVE AVAILABILITY ENGINE"""
    while True:
        try:
            await discovery_engine.sync_all()
            logger.info("SYNC_CYCLE_COMPLETED")
        except Exception as e:
            logger.error("SYNC_CYCLE_FAILED", error=str(e))
        await asyncio.sleep(60)

async def hold_swapper_loop():
    """PILLAR 3: TOKEN MASTER (SMOOTH SWAP)"""
    swapper = HoldSwapper()
    try:
        await swapper.monitor_and_swap()
    except Exception as e:
        logger.warning(f"[HOLD_SWAPPER] loop error: {e}")

async def ghost_monitor_loop():
    """PILLAR 4: THE GHOST MONITOR"""
    from services.monitor.ghost import GHOST_SCAN_INTERVAL
    while True:
        try:
            async with AsyncSessionLocal() as db:
                monitor = GhostMonitor(db)
                await monitor.scan_once()
        except Exception as e:
            logger.warning(f"[GHOST_MONITOR] iteration error: {e}")
        await asyncio.sleep(GHOST_SCAN_INTERVAL)

# ------------------------------------------------------------------------------
# 5. Service Launchers & External Tunnel Orchestrator
# ------------------------------------------------------------------------------
def setup_external_tunnels(open_tunnel: bool = False, dual_tunnels: bool = False):
    """
    Sets up external public tunnels (Localtunnel) targeting Streamlit UI (Port 8501)
    and optionally FastAPI Backend (Port 8000). Guarantees that public links point
    to actual external domains, NOT localhost.
    """
    in_colab = "google.colab" in sys.modules
    should_run = open_tunnel or in_colab or dual_tunnels

    if not should_run:
        return

    print("\n" + "=" * 70)
    print("🌐 INITIATING EXTERNAL TUNNEL ORCHESTRATION (LOCALTUNNEL)")
    print("=" * 70)

    # 1. Primary: Start Streamlit GUI tunnel on Port 8501
    st_url = tunnel_manager.start_localtunnel(STREAMLIT_PORT, "streamlit")

    # 2. Secondary: If dual requested or Colab, start API tunnel on Port 8000
    if dual_tunnels or in_colab:
        api_url = tunnel_manager.start_localtunnel(API_PORT, "api")
    else:
        api_url = tunnel_manager.get_tunnel_url("api")

    print("=" * 70)
    if st_url:
        print(f"🚀 STREAMLIT FRONTEND TUNNEL: {st_url}")
    else:
        print(f"⏳ STREAMLIT TUNNEL: In background / run 'npx localtunnel --port {STREAMLIT_PORT}'")

    if api_url:
        print(f"⚙️  FASTAPI BACKEND TUNNEL:   {api_url}/api")
    print("=" * 70 + "\n")

def run_streamlit_process(port: int = STREAMLIT_PORT):
    """
    Launches the Streamlit GUI in a dedicated process with CORS and XSRF disabled
    to allow seamless mobile access through localtunnel and external proxies.
    """
    ui_app_path = PROJECT_ROOT / "apps" / "ui" / "app.py"
    if not ui_app_path.exists():
        ui_app_path = PROJECT_ROOT / "main.py"

    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(ui_app_path),
        f"--server.port={port}",
        f"--server.address={STREAMLIT_HOST}",
        "--server.headless=true",
        "--server.enableCORS=false",
        "--server.enableXsrfProtection=false",
        "--browser.gatherUsageStats=false"
    ]
    print(f"[STREAMLIT_PROCESS] Launching Streamlit GUI on port {port} (CORS & XSRF disabled for tunnel compatibility)...")
    try:
        # Child process inherits PYTHONPATH pointing to PROJECT_ROOT
        env = os.environ.copy()
        env["PYTHONPATH"] = f"{root_str}{os.pathsep}{env.get('PYTHONPATH', '')}".rstrip(os.pathsep)
        proc = subprocess.Popen(cmd, env=env)
        return proc
    except Exception as e:
        print(f"[STREAMLIT_ERROR] Failed to spawn streamlit process: {e}")
        return None

async def run_api_server():
    """Runs the FastAPI Backend API Server with dedicated /api routing"""
    try:
        import uvicorn
        config = uvicorn.Config(
            api_app,
            host=API_HOST,
            port=API_PORT,
            log_level="info",
            access_log=False
        )
        server = uvicorn.Server(config)
        print(f"[API_SERVER] Backend API running at http://{API_HOST}:{API_PORT}/api")
        await server.serve()
    except ImportError:
        print("[WARN] Uvicorn not installed. Running background bot in standalone mode.")
        await start_bot()
    except Exception as e:
        print(f"[API_ERROR] Backend server failure: {e}")

async def run_unified_ecosystem(open_tunnel: bool = False, dual_tunnels: bool = False):
    """
    Main Orchestrator:
    1. Safe port allocation check (no conflicts between API and Streamlit).
    2. Initializes Database.
    3. Spawns Streamlit GUI on Port 8501 (Main UI Route).
    4. Orchestrates external public tunnels (Localtunnel).
    5. Starts Backend API on Port 8000 under /api with smart mobile routing.
    6. Starts Bot and autonomous Sniper loops.
    """
    lan_ip = get_lan_ip()

    print("\n" + "=" * 75)
    print("🎯 WEBOOK INGESTION & SNIPER PLATFORM - DECOUPLED ARCHITECTURE")
    print("=" * 75)
    print(f"🖥️  Streamlit UI (Main Frontend):  http://localhost:{STREAMLIT_PORT}")
    print(f"📱  Streamlit UI (Local WiFi/LAN): http://{lan_ip}:{STREAMLIT_PORT}")
    print(f"⚙️  Backend API (Dedicated Path):  http://localhost:{API_PORT}/api")
    print(f"📚  API Documentation (Swagger):   http://localhost:{API_PORT}/docs")
    print(f"🔄  Dynamic Gateway:              http://localhost:{API_PORT}/ -> Smart Tunnel Resolver")
    print("=" * 75 + "\n")

    # 1. Initialize Database Tables
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database_Tables_Initialized")
    except Exception as e:
        logger.warning(f"Database initialization note: {e}")

    # 2. Launch Streamlit UI process (Port 8501)
    streamlit_proc = run_streamlit_process(port=STREAMLIT_PORT)

    # 3. Setup External Public Tunnels if requested or in Colab
    setup_external_tunnels(open_tunnel=open_tunnel, dual_tunnels=dual_tunnels)

    # 4. Run API Server + All Background Tasks concurrently (Bot, Sync, Ghost Monitor, Hold Swapper)
    bot_task = asyncio.create_task(start_bot())
    sync_task = asyncio.create_task(background_sync_loop())
    ghost_task = asyncio.create_task(ghost_monitor_loop())
    swapper_task = asyncio.create_task(hold_swapper_loop())

    print("[ORCHESTRATOR] Concurrently launching API server, Telegram bot, and all background discovery engines...")

    try:
        await asyncio.gather(
            run_api_server(),
            bot_task,
            sync_task,
            ghost_task,
            swapper_task,
            return_exceptions=True
        )
    finally:
        if streamlit_proc and streamlit_proc.poll() is None:
            print("[SHUTDOWN] Terminating Streamlit UI process...")
            streamlit_proc.terminate()
        tunnel_manager.stop_all()

# ------------------------------------------------------------------------------
# 6. Streamlit Execution Support (If run via: streamlit run main.py)
# ------------------------------------------------------------------------------
if "streamlit" in sys.modules or any("streamlit" in arg for arg in sys.argv):
    try:
        from apps.ui.app import *
    except Exception as _st_err:
        import streamlit as st
        st.title("🎯 Webook Ingestion & Sniper Platform")
        st.info("Streamlit GUI active. Loading control center...")

async def main():
    """Programmatic entrypoint for external orchestrators and Google Colab."""
    await run_unified_ecosystem()

# ------------------------------------------------------------------------------
# 7. CLI Entrypoint
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    if not any("streamlit" in arg for arg in sys.argv):
        parser = argparse.ArgumentParser(description="Webook Ingestion & Sniper Control Platform")
        parser.add_argument(
            "--mode",
            choices=["all", "api", "ui"],
            default="all",
            help="Execution mode: 'all' (API + Streamlit UI), 'api' (Backend only), 'ui' (Streamlit only)"
        )
        parser.add_argument(
            "--tunnel",
            action="store_true",
            help="Expose Streamlit UI directly via public tunnel (Port 8501)"
        )
        parser.add_argument(
            "--dual-tunnels",
            action="store_true",
            help="Expose BOTH Streamlit UI (Port 8501) and API (Port 8000) via separate public tunnels"
        )
        parser.add_argument(
            "--streamlit-url",
            type=str,
            default=None,
            help="Pre-configured external Streamlit URL (e.g. https://xxx.loca.lt)"
        )
        parser.add_argument(
            "--api-port",
            type=int,
            default=API_PORT,
            help=f"Custom Backend API port (default: {API_PORT})"
        )
        parser.add_argument(
            "--ui-port",
            type=int,
            default=STREAMLIT_PORT,
            help=f"Custom Streamlit UI port (default: {STREAMLIT_PORT})"
        )
        args, _ = parser.parse_known_args()

        if args.api_port:
            API_PORT = args.api_port
        if args.ui_port:
            STREAMLIT_PORT = args.ui_port

        # Re-verify port safety with user CLI overrides
        API_PORT, STREAMLIT_PORT = resolve_non_conflicting_ports(API_PORT, STREAMLIT_PORT)
        os.environ["API_PORT"] = str(API_PORT)
        os.environ["STREAMLIT_PORT"] = str(STREAMLIT_PORT)

        if args.streamlit_url:
            tunnel_manager.set_tunnel_url("streamlit", args.streamlit_url)

        try:
            if args.mode == "ui":
                print(f"[MODE] Starting Streamlit GUI solely on port {STREAMLIT_PORT}...")
                proc = run_streamlit_process(port=STREAMLIT_PORT)
                if proc:
                    proc.wait()
            elif args.mode == "api":
                print(f"[MODE] Starting Backend API solely on port {API_PORT} (path prefix /api)...")
                asyncio.run(run_api_server())
            else:
                # Mode 'all' (Default)
                asyncio.run(run_unified_ecosystem(
                    open_tunnel=args.tunnel,
                    dual_tunnels=args.dual_tunnels
                ))
        except KeyboardInterrupt:
            print("\n[SYSTEM] Graceful shutdown completed.")
        except Exception as e:
            print(f"[FATAL_ERROR] {e}")
