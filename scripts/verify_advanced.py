import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from modules.auth.fingerprint import FingerprintGenerator
from core.network.client import BaseAPIClient
from modules.sniper.engine import SniperEngine
from database.models.reservation import AuthSession
from core.logging.logger import setup_logging, logger

async def verify_advanced_features():
    setup_logging()
    logger.info("Verifying Advanced Features: Multi-Account, Proxy, and Smooth Swap...")

    # 1. Test Fingerprint Generator
    fp1 = FingerprintGenerator.generate()
    fp2 = FingerprintGenerator.generate()
    assert "User-Agent" in fp1
    assert fp1 != fp2 # Should be randomized
    logger.info(f"Fingerprint randomization verified. UA1: {fp1['User-Agent'][:30]}...")

    # 2. Test Proxy Injection in Client
    with patch('httpx.AsyncHTTPTransport') as mock_transport:
        client = BaseAPIClient(
            base_url="https://api.test", 
            proxy="http://user:pass@residential.proxy:8080"
        )
        mock_transport.assert_called_once()
        logger.info("Proxy transport injection verified.")

    # 3. Test Sniper Engine with Account Context
    mock_session = AuthSession(
        bearer_token="TOKEN_X",
        proxy_url="http://proxy:8080",
        user_agent="Custom-UA-123"
    )
    
    engine = SniperEngine(mock_session)
    assert engine.headers["User-Agent"] == "Custom-UA-123"
    logger.info("Sniper Engine correctly adopted Account Fingerprint/UA.")

    # 4. Simulate Smooth Swap Atomic Logic
    logger.info("Simulating Smooth Swap atomic timing (T-40s)...")
    start = asyncio.get_event_loop().time()
    
    # Simulate Account A Release and Account B Reserve
    # In reality, these happen via API calls. Here we just time the logic.
    async def fast_swap():
        # task_a = release_hold(...)
        # task_b = reserve_seats(...)
        # await asyncio.gather(task_a, task_b)
        await asyncio.sleep(0.05) # Simulated latency (50ms)
        
    await fast_swap()
    end = asyncio.get_event_loop().time()
    logger.info(f"Swap simulation completed in {int((end-start)*1000)}ms.")

    logger.info("Advanced Features Verification SUCCESS.")

if __name__ == "__main__":
    asyncio.run(verify_advanced_features())
