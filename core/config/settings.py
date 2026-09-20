# core/config/settings.py
import os

class Settings:
    def __init__(self):
        self.api_host: str = os.getenv("API_HOST", "0.0.0.0")
        self.api_port: int = int(os.getenv("API_PORT", "8000"))
        self.database_url: str = os.getenv(
            "DATABASE_URL", 
            "sqlite+aiosqlite:///./webook_local.db"
        )
        self.redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.environment: str = os.getenv("ENV", "development")

settings = Settings()
