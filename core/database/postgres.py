from sqlalchemy import event
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from core.config.settings import settings

# Create Async Engine with SQLite safety
engine_args = {}
if "sqlite" not in settings.database_url:
    engine_args.update({
        "pool_size": 20,
        "max_overflow": 0
    })
else:
    engine_args.update({
        "connect_args": {"timeout": 30},
    })

engine = create_async_engine(
    settings.database_url,
    **engine_args
)

if "sqlite" in settings.database_url:
    @event.listens_for(engine.sync_engine, "connect")
    def _set_slite_pragmas(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=30000")
        
        # FORENSIC TELEMETRY INJECTION
        try:
            # Check if table exists before querying
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='live_events'")
            if cursor.fetchone():
                cursor.execute("SELECT COUNT(*) FROM live_events")
                total = cursor.fetchone()[0]
                # ... other counts ...
                import json
                evidence = {
                    "total_events": total,
                    "timestamp": __import__('datetime').datetime.now().isoformat()
                }
                with open("forensic_evidence.json", "w") as f:
                    json.dump(evidence, f)
        except Exception:
            pass 
            
        cursor.close()

# Create Async Session Factory
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
