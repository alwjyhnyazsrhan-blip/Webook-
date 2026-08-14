from typing import Dict, Any, Optional
from core.network.client import BaseAPIClient
from core.network.endpoints import WebookEndpoints
from core.logging.logger import logger

class WebookAuthClient(BaseAPIClient):
    """
    Production Webook Authentication Client.
    Handles the real multi-step OTP login flow.
    """

    def __init__(self, proxy: Optional[str] = None):
        super().__init__(base_url=WebookEndpoints.BASE_URL, proxy=proxy)
        self._login_device_token = None
        self._standard_device_token = None
        try:
            from core.config.settings import settings as app_settings
            self._login_device_token = app_settings.login_device_token
            self._standard_device_token = app_settings.standard_device_token
        except Exception:
            self._login_device_token = "bqvtwD2zBdLC8HkUIsvwmlhMnkfifLtffml2mNNRevDnb25yn5Axw2zqtwB8zvB0"  # FIX: was truncated, must match spec exactly
            self._standard_device_token = "ce492c7f756978ba98da0627544f69fbc76aae789bdab3f241d111d8642416db"

    async def request_otp(self, email: str) -> bool:
        """
        Step 1: Request OTP from Webook server.
        """
        headers = {
            "token": self._login_device_token,  # FIX: API spec header is 'token', not 'device-token'
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        payload = {"email": email, "lang": "ar"}  # FIX: lang* is a required field per API spec
        
        logger.info(f"Requesting OTP for {email}")
        response = await self.request("POST", WebookEndpoints.LOGIN_OTP_REQUEST, json=payload, headers=headers)
        
        if response.status_code == 200:
            logger.info("OTP request successful.")
            return True
        return False

    async def verify_otp(self, email: str, otp: str) -> Dict[str, Any]:
        """
        Step 2: Verify OTP and get the bearer_token.
        """
        headers = {
            "token": self._login_device_token,  # FIX: API spec header is 'token', not 'device-token'
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        payload = {
            "email": email,
            "otp": otp
        }
        
        logger.info(f"Verifying OTP for {email}")
        response = await self.request("POST", WebookEndpoints.LOGIN_VERIFY_OTP, json=payload, headers=headers)
        
        # This will contain the 'token' field if successful
        data = response.json()
        if "token" in data:
            logger.info("Authentication successful. Bearer token obtained.")
            return data
        
        raise Exception(f"OTP verification failed: {data.get('message', 'Unknown error')}")

    def get_standard_headers(self, bearer_token: str) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {bearer_token}",
            "token": self._standard_device_token,  # FIX: API spec header is 'token', not 'device-token'
            "Accept": "application/json"
        }
