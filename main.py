print("MAIN_LOADED")
import asyncio
import uvicorn
from apps.api.main import app as api_app
from apps.bot.main import start_bot
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

# NOTE: ReservationWorker runs ONLY in apps/worker/main.py (dedicated container).
# It is intentionally NOT started here to prevent duplicate task processing and
# race conditions between the app container and the worker container.

async def hold_swapper_loop():
    """PILLAR 3: TOKEN MASTER (SMOOTH SWAP)"""
    swapper = HoldSwapper()
    await swapper.monitor_and_swap()

async def ghost_monitor_loop():
    """PILLAR 4: THE GHOST MONITOR â€” per-iteration session to prevent connection leak."""
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
    api_server = uvicorn.Server(uvicorn.Config(api_app, host=settings.api_host, port=settings.api_port, log_level="info"))

    bot_task = asyncio.create_task(start_bot())

    try:
        await asyncio.gather(
            api_server.serve(),
            bot_task,
        )
    except Exception as e:
        logger.error("SYSTEM_FAILURE", error=str(e))

if __name__ == "__main__":
    try:
        asyncio.run(run_services())
    except KeyboardInterrupt:
        logger.info("SYSTEM_SHUTDOWN")
    except Exception as e:
        logger.error("UNHANDLED_EXCEPTION", error=str(e))
