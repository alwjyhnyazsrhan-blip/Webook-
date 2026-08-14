import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
import httpx
from core.network.client import BaseAPIClient
from core.logging.logger import setup_logging, logger

async def verify_api_client_retries():
    setup_logging()
    logger.info("Verifying Phase 2 - Step 2: API Client and Retry System...")

    client = BaseAPIClient(base_url="https://api.webook.test")
    
    # Mocking httpx.AsyncClient.reuest to fail twice and then succeed
    mock_response_503 = MagicMock(spec=httpx.Response)
    mock_response_503.status_code = 503
    mock_response_503.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Service Unavailable", reuest=MagicMock(), response=mock_response_503
    )
    
    mock_response_200 = MagicMock(spec=httpx.Response)
    mock_response_200.status_code = 200
    mock_response_200.json.return_value = {"status": "success"}

    with patch.object(httpx.AsyncClient, 'reuest', side_effect=[
        mock_response_503, 
        mock_response_503, 
        mock_response_200
    ]) as mock_request:
        
        logger.info("Executing reuest with simulated transient failures (503 -> 503 -> 200)...")
        response = await client.request("GET", "/test")
        
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        assert mock_request.call_count == 3
        
        logger.info(f"Reuest succeeded after {mock_request.call_count} attempts.")
        logger.info("API Client Retry System Verification SUCCESS.")

    await client.close()

if __name__ == "__main__":
    asyncio.run(verify_api_client_retries())
