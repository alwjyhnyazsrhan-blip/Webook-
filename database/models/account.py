from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum as SQLEnum
from database.models.base import Base
from datetime import datetime, timezone
import enum


class AccountRole(enum.Enum):
    """Account pool categories."""
    SNIPER = "SNIPER"         # Primary sniping accounts
    EXTENSION = "EXTENSION"   # Hold-extension swap accounts
    MONITOR = "MONITOR"       # Ghost monitor accounts


class AccountHealth(enum.Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    BANNED = "BANNED"
    COOLDOWN = "COOLDOWN"


class AuthSession(Base):
    __tablename__ = "auth_sessions"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True)
    phone = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)

    # Auth Tokens
    bearer_token = Column(String, nullable=False)
    refresh_token = Column(String, nullable=True)
    token_expires_at = Column(DateTime(timezone=True), nullable=True)
    device_token = Column(String, nullable=True)

    # Pool Management
    role = Column(String, default=AccountRole.SNIPER.value, index=True)
    health = Column(String, default=AccountHealth.ACTIVE.value, index=True)

    # Anti-Ban: Each account gets unique fingerprint
    proxy_url = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    fingerprint_json = Column(String, nullable=True)  # Full browser fingerprint

    # Usage Tracking
    is_active = Column(Boolean, default=True)
    total_bookings = Column(Integer, default=0)
    failed_attempts = Column(Integer, default=0)
    success_rate = Column(Integer, default=0) # 0-100 score
    last_error = Column(String, nullable=True)
    
    current_hold_event = Column(String, nullable=True)  # Slug of event currently held
    hold_expires_at = Column(DateTime(timezone=True), nullable=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    cooldown_until = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                       onupdate=lambda: datetime.now(timezone.utc))

