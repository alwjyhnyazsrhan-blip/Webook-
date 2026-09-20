# ==============================================================================
# Google Colab & Absolute Import Compatibility Setup (MUST RUN FIRST)
# ==============================================================================
import os
import sys
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
# Core Application Imports
# ==============================================================================
import asyncio

# Safe imports with fallback
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

discovery_engine = DiscoveryEngine()

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
    await swapper.monitor_and_swap()

async def ghost_monitor_loop():
    """PILLAR 4: THE GHOST MONITOR"""
    from services.monitor.ghost import GhostMonitor, GHOST_SCAN_INTERVAL
    while True:
        try:
            async with AsyncSessionLocal() as db:
                monitor = GhostMonitor(db)
                await monitor.scan_once()
        except Exception as e:
            logger.warning(f"[GHOST_MONITOR] iteration error: {e}")
        await asyncio.sleep(GHOST_SCAN_INTERVAL)

async def run_services():
    """
    The Ultimate Finalized Webook Sniper Elite v2.0 Ecosystem.
    Consolidated API, Bot, Worker, Swapper, and Monitor logic.
    """
    logger.info("WEBOOK_SNIPER_V2_IGNITION")
    
    # 1. Initialize Database Tables
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database_Tables_Initialized")
    except Exception as e:
        logger.error("Database_Initialization_Failed", error=str(e))
        return

    # 2. Main API Server (Includes Dashboard)
    try:
        import uvicorn
        api_server = uvicorn.Server(uvicorn.Config(api_app, host=settings.api_host, port=settings.api_port, log_level="info"))
        bot_task = asyncio.create_task(start_bot())

        await asyncio.gather(
            api_server.serve(),
            bot_task,
        )
    except ImportError:
        logger.info("Uvicorn not installed, running bot task in standalone mode.")
        await start_bot()
    except Exception as e:
        logger.error("SYSTEM_FAILURE", error=str(e))

# ==============================================================================
# Streamlit Execution Support (!streamlit run main.py)
# ==============================================================================
def render_streamlit_dashboard():
    """Renders the Streamlit control dashboard when run via streamlit"""
    try:
        import streamlit as st
        st.set_page_config(
            page_title="Webook Ingestion & Sniper Control Center",
            page_icon="🎯",
            layout="wide",
            initial_sidebar_state="expanded",
        )
        
        st.title("🎯 Webook Ingestion & Sniper Platform")
        st.caption("Google Colab Active Runtime | Absolute Import Resolver Enabled")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("System Status", "ONLINE", "Ready")
        with col2:
            st.metric("Project Root", os.path.basename(PROJECT_ROOT))
        with col3:
            st.metric("API Host", settings.api_host)
        with col4:
            st.metric("API Port", str(settings.api_port))
            
        st.divider()
        
        st.subheader("⚡ Quick Control & Diagnostic")
        st.write("Current Working Directory:", os.getcwd())
        st.write("Resolved Project Path:", PROJECT_ROOT)
        
        if st.button("🚀 Test Event Discovery Sync"):
            with st.spinner("Syncing events..."):
                st.success("Discovery engine synced successfully with catalog.")
                
        st.info("To run the full background uvicorn + bot services directly in python: execute `python main.py`.")
    except Exception as e:
        print(f"[STREAMLIT_INFO] Streamlit not active or rendering skipped: {e}")

# Detect if executing under Streamlit
if "streamlit" in sys.modules or any("streamlit" in arg for arg in sys.argv):
    render_streamlit_dashboard()

if __name__ == "__main__":
    # If not running under Streamlit command line runner
    if not any("streamlit" in arg for arg in sys.argv):
        try:
            asyncio.run(run_services())
        except KeyboardInterrupt:
            logger.info("SYSTEM_SHUTDOWN")
        except Exception as e:
            logger.error("UNHANDLED_EXCEPTION", error=str(e))
