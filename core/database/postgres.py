# core/database/postgres.py
import os
import contextlib

try:
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker

    db_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./webook_local.db")
    engine = create_async_engine(db_url, echo=False)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

except ImportError:
    # Lightweight mock for environments without SQLAlchemy
    class MockEngine:
        @contextlib.asynccontextmanager
        async def begin(self):
            class MockConn:
                async def run_sync(self, fn, *args, **kwargs):
                    pass
            yield MockConn()

    class MockSession:
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            pass

    engine = MockEngine()
    def AsyncSessionLocal():
        return MockSession()
