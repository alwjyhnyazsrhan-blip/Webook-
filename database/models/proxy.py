from sqlalchemy import Column, Integer, String, Boolean, DateTime
from database.models.base import Base
from datetime import datetime, timezone

class ProxyPool(Base):
    __tablename__ = "proxy_pool"

    id = Column(Integer, primary_key=True)
    url = Column(String, unique=True, nullable=False) # http://user:pass@host:port
    is_alive = Column(Boolean, default=True)
    latency = Column(Integer, nullable=True) # in ms
    last_check_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    fail_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

