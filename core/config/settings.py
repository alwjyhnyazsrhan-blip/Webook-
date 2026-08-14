import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

class Settings:
    def __init__(self):
        self.app_name = os.getenv("APP_NAME", "Webook Sniper Platform")
        self.debug = os.getenv("DEBUG", "true").lower() == "true"
        self.bot_token = os.getenv("BOT_TOKEN", "123:ABC")
        
        admin_ids_raw = os.getenv("ADMIN_IDS", "[]")
        self.admin_ids = [int(i.strip()) for i in admin_ids_raw.strip("[]").split(",") if i.strip()]
        
        self.database_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/webook.db")
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.log_level = os.getenv("LOG_LEVEL", "DEBUG")
        self.json_logs = os.getenv("JSON_LOGS", "false").lower() == "true"
        self.api_host = os.getenv("API_HOST", "0.0.0.0")
        self.api_port = int(os.getenv("API_PORT", "8000"))
        self.capsolver_api_key = os.getenv("CAPSOLVER_API_KEY", "")
        self.turnstile_sitekey = os.getenv(
            "TURNSTILE_SITEKEY",
            "0x4AAAAAAAEHcP_mgMtMABCk",
        )
        self.webook_api_token = os.getenv(
            "WEBOOK_API_TOKEN",
            "e9aac1f2f0b6c07d6be070ed14829de684264278359148d6a582ca65a50934d2",
        )
        self.login_device_token = os.getenv(
            "LOGIN_DEVICE_TOKEN",
            "bvtwD2zBdLC8HkUIsvwmlhMnkfifLtffml2mNNRe",
        )
        self.standard_device_token = os.getenv(
            "STANDARD_DEVICE_TOKEN",
            "ce492c7f756978ba98da0627544f69fbc76aae789bdab3f241d111d8642416db",
        )

settings = Settings()
