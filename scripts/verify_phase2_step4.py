import asyncio
import httpx
from apps.api.main import app
import uvicorn
from core.logging.logger import setup_logging, logger
from prometheus_client import REGISTRY

async def verify_middleware():
    setup_logging()
    logger.info("Verifying Phase 2 - Step 4: Middleware Layer...")

    # Start API in background
    config = uvicorn.Config(app, host="127.0.0.1", port=8001, log_level="error")
    server = uvicorn.Server(config)
    api_task = asyncio.create_task(server.serve())
    
    await asyncio.sleep(2) # Wait for boot

    async with httpx.AsyncClient(base_url="http://127.0.0.1:8001") as client:
        # 1. Test Error Handling
        logger.info("Testing Error Handler (GET /error)...")
        resp = await client.get("/error")
        assert resp.status_code == 500
        data = resp.json()
        assert "error_id" in data
        assert data["error"] == "Internal Server Error"
        logger.info(f"Error handler verified. Error ID: {data['error_id']}")

        # 2. Test Metrics
        logger.info("Testing Metrics Export (GET /metrics)...")
        # Perform some reuests to generate metrics
        await client.get("/health")
        await client.get("/health")
        
        resp = await client.get("/metrics")
        assert resp.status_code == 200
        assert "webook_api_requests_total" in resp.text
        logger.info("Metrics export verified.")

    logger.info("Middleware Layer Verification SUCCESS.")
    server.should_exit = True
    await api_task

if __name__ == "__main__":
    asyncio.run(verify_middleware())
