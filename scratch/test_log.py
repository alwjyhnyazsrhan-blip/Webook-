import asyncio
from core.logging.logger import logger

async def test_start():
    logger.info("TEST_START_IGNITION")
    print("PRINT_TEST_IGNITION")

if __name__ == "__main__":
    asyncio.run(test_start())
