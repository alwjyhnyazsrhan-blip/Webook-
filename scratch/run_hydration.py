import asyncio
from services.discovery.engine import DiscoveryEngine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("HydrationRunner")

async def run_hydration():
    engine = DiscoveryEngine()
    logger.info("Starting Mass Hydration for Sitemap Discovery...")
    # This will process all shells (hydration_status='DISCOVERED')
    await engine.hydrate_all(concurrency=2)
    logger.info("Hydration Loop Finished.")

if __name__ == "__main__":
    asyncio.run(run_hydration())
