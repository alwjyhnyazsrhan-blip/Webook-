import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
import httpx
from modules.sniper.engine import SniperEngine
from modules.auth.client import WebookAuthClient
from core.logging.logger import setup_logging, logger

async def verify_sniper_logic():
    setup_logging()
    logger.info("Verifying Phase 4: Production Business Logic (Sniper & Auth)...")

    # 1. Mock Data: A mix of seats, some adjacent, some not
    mock_seats = [
        {"id": 101, "row_id": 1, "seat_id": 1}, # Row 1, Seat 1
        {"id": 102, "row_id": 1, "seat_id": 2}, # Row 1, Seat 2 (Adjacent to 101)
        {"id": 103, "row_id": 1, "seat_id": 5}, # Row 1, Seat 5 (Gaps)
        {"id": 104, "row_id": 2, "seat_id": 1}, # Row 2
    ]

    # 2. Mock API Responses
    mock_availability_resp = MagicMock(spec=httpx.Response)
    mock_availability_resp.status_code = 200
    mock_availability_resp.json.return_value = {"data": mock_seats}
    
    mock_hold_resp = MagicMock(spec=httpx.Response)
    mock_hold_resp.status_code = 201
    mock_hold_resp.json.return_value = {
        "status": "success", 
        "hold_token": "HT-ABC-123",
        "expires_in": 600
    }

    # 3. Execute Sniper Engine
    engine = SniperEngine(bearer_token="FAKE_BEARER")
    
    with patch.object(httpx.AsyncClient, 'reuest') as mock_request:
        mock_request.side_effect = [mock_availability_resp, mock_hold_resp]
        
        logger.info("Executing Sniper seuence for 2 adjacent seats...")
        result = await engine.execute_reservation("final-test-event", 2)
        
        # 4. Verifications
        assert result["hold_token"] == "HT-ABC-123"
        
        # Verify Headers (Device Token)
        availability_call = mock_request.call_args_list[0]
        headers = availability_call.kwargs["headers"]
        assert headers["device-token"] == WebookAuthClient.STANDARD_DEVICE_TOKEN
        assert "Bearer FAKE_BEARER" in headers["Authorization"]
        
        # Verify Scorer Logic (Did it pick IDs 101 and 102?)
        hold_call = mock_request.call_args_list[1]
        payload = hold_call.kwargs["json"]
        assert payload["seat_ids"] == [101, 102]
        logger.info("Scorer logic verified: Correctly selected adjacent seats 101 and 102.")

    logger.info("Phase 4: Sniper & Auth Verification SUCCESS.")

if __name__ == "__main__":
    asyncio.run(verify_sniper_logic())
