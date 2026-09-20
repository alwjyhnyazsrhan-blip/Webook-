# ==============================================================================
# Google Colab & Absolute Import Compatibility Setup (MUST RUN FIRST)
# ==============================================================================
import os
import sys
import argparse
import subprocess
import asyncio
import threading
import time
from pathlib import Path

# Dynamically resolve absolute project root directory
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
PARENT_DIR = os.path.dirname(PROJECT_ROOT)
CWD = os.getcwd()

# Inject project root and common subdirectories into sys.path
for path_entry in [PROJECT_ROOT, PARENT_DIR, CWD]:
    if path_entry and path_entry not in sys.path:
        sys.path.insert(0, path_entry)

# Ensure PYTHONPATH environment variable is set for sub-processes and workers
current_pythonpath = os.environ.get("PYTHONPATH", "")
if PROJECT_ROOT not in current_pythonpath.split(os.pathsep):
    os.environ["PYTHONPATH"] = f"{PROJECT_ROOT}{os.pathsep}{current_pythonpath}" if current_pythonpath else PROJECT_ROOT

print(f"[PATH_CONFIG] Absolute project root configured: {PROJECT_ROOT}")
print(f"[PATH_CONFIG] sys.path[0]: {sys.path[0]}")
print("MAIN_LOADED")

# ==============================================================================
# Core Application Imports & Fallbacks
# ==============================================================================
try:
    from apps.api.main import app as api_app
except ModuleNotFoundError as e:
    print(f"[WARN] apps.api.main import fallback: {e}")
    from fastapi import FastAPI
    api_app = FastAPI()

try:
    from apps.bot.main import start_bot
except ModuleNotFoundError as e:
    print(f"[WARN] apps.bot.main import fallback: {e}")
    async def start_bot():
        print("[BOT] Mock bot started")

from core.config.settings import settings
from core.logging.logger import logger
from database.models import Base
from core.database.postgres import engine, AsyncSessionLocal
from services.discovery.engine import DiscoveryEngine
from services.reservation.swapper import HoldSwapper
from services.monitor.ghost import GhostMonitor

# Port Configuration
API_PORT = int(os.getenv("API_PORT", str(getattr(settings, "api_port", 8000))))
API_HOST = os.getenv("API_HOST", getattr(settings, "api_host", "0.0.0.0"))
STREAMLIT_PORT = int(os.getenv("STREAMLIT_PORT", "8501"))
STREAMLIT_HOST = os.getenv("STREAMLIT_HOST", "0.0.0.0")

discovery_engine = DiscoveryEngine()

# ==============================================================================
# Background Service Loops
# ==============================================================================
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

# ==============================================================================
# Service Launchers (Decoupled API & Streamlit)
# ==============================================================================
def start_tunnel_if_requested(target_port: int = 8501):
    """
    Starts a Cloudflared or Localtunnel tunnel targeting the Streamlit UI (Port 8501)
    so the public URL opens the graphical interface directly instead of raw JSON.
    """
    try:
        print(f"\n[TUNNEL] Setting up public tunnel to Streamlit UI on Port {target_port}...")
        # Check if running in Google Colab
        in_colab = "google.colab" in sys.modules
        
        # Check for pyngrok or cloudflared
        try:
            from pyngrok import ngrok
            tunnel = ngrok.connect(target_port)
            print(f"======================================================================")
            print(f"🚀 PUBLIC TUNNEL ACTIVE (Streamlit GUI): {tunnel.public_url}")
            print(f"======================================================================")
            return tunnel.public_url
        except Exception:
            pass
            
        print(f"[TUNNEL] To expose Streamlit UI via cloudflared: npx localtunnel --port {target_port}")
    except Exception as e:
        print(f"[TUNNEL INFO] Tunnel setup skipped or manual: {e}")
    return None

def run_streamlit_process(port: int = STREAMLIT_PORT):
    """Launches the Streamlit GUI in a dedicated process on Port 8501"""
    ui_app_path = os.path.join(PROJECT_ROOT, "apps", "ui", "app.py")
    if not os.path.exists(ui_app_path):
        # Fallback to main.py
        ui_app_path = os.path.join(PROJECT_ROOT, "main.py")
        
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        ui_app_path,
        f"--server.port={port}",
        f"--server.address={STREAMLIT_HOST}",
        "--server.headless=true",
        "--browser.gatherUsageStats=false"
    ]
    print(f"[STREAMLIT_PROCESS] Launching Streamlit GUI on port {port}...")
    try:
        proc = subprocess.Popen(cmd, env=os.environ.copy())
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

async def run_unified_ecosystem(open_tunnel: bool = False):
    """
    Main Orchestrator:
    1. Initializes Database
    2. Spawns Streamlit GUI on Port 8501 (Main UI Route)
    3. Starts Backend API on Port 8000 under /api
    4. Starts Bot and autonomous Sniper loops
    """
    print("\n" + "=" * 70)
    print("🎯 WEBOOK INGESTION & SNIPER PLATFORM - DECOUPLED ARCHITECTURE")
    print("=" * 70)
    print(f"🖥️  Streamlit UI (Main Frontend):  http://localhost:{STREAMLIT_PORT}")
    print(f"⚙️  Backend API (Dedicated Path):  http://localhost:{API_PORT}/api")
    print(f"📚  API Documentation (Swagger):   http://localhost:{API_PORT}/docs")
    print(f"🔄  Auto-Redirect:                 http://localhost:{API_PORT}/ -> Streamlit ({STREAMLIT_PORT})")
    print("=" * 70 + "\n")

    # 1. Initialize Database Tables
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database_Tables_Initialized")
    except Exception as e:
        logger.warning(f"Database initialization note: {e}")

    # 2. Launch Streamlit UI process (Port 8501)
    streamlit_proc = run_streamlit_process(port=STREAMLIT_PORT)

    # 3. Setup Tunnel to Streamlit UI if requested or in Colab
    if open_tunnel or "google.colab" in sys.modules:
        start_tunnel_if_requested(target_port=STREAMLIT_PORT)

    # 4. Run API Server + Background Tasks concurrently
    bot_task = asyncio.create_task(start_bot())
    sync_task = asyncio.create_task(background_sync_loop())
    
    try:
        await asyncio.gather(
            run_api_server(),
            bot_task,
            sync_task,
            return_exceptions=True
        )
    finally:
        if streamlit_proc and streamlit_proc.poll() is None:
            print("[SHUTDOWN] Terminating Streamlit UI process...")
            streamlit_proc.terminate()

# ==============================================================================
# Streamlit Execution Support (If run via: streamlit run main.py)
# ==============================================================================
if "streamlit" in sys.modules or any("streamlit" in arg for arg in sys.argv):
    try:
        from apps.ui.app import *
    except Exception as _st_err:
        import streamlit as st
        st.title("🎯 Webook Ingestion & Sniper Platform")
        st.info("Streamlit GUI active. Loading control center...")

# ==============================================================================
# CLI Entrypoint
# ==============================================================================
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
                asyncio.run(run_unified_ecosystem(open_tunnel=args.tunnel))
        except KeyboardInterrupt:
            print("\n[SYSTEM] Graceful shutdown completed.")
        except Exception as e:
            print(f"[FATAL_ERROR] {e}")
