from sqlalchemy import Column, BigInteger, Integer, String, Boolean, ForeignKey, JSON, DateTime
from sqlalchemy.orm import relationship
from database.models.base import Base
from datetime import datetime, timezone

class UserEventSubscription(Base):
    __tablename__ = 'user_event_subscriptions'

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, index=True)
    event_id = Column(Integer, ForeignKey('live_events.id'), nullable=False)
    
    track_updates = Column(Boolean, default=True)
    track_tickets = Column(Boolean, default=True)
    receive_notifications = Column(Boolean, default=True)
    reminder_time_hours = Column(Integer, default=24)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_sync_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    event = relationship("LiveEvent")

class UserGlobalPrefs(Base):
    __tablename__ = 'user_global_prefs'

    user_id = Column(BigInteger, primary_key=True)
    language = Column(String, default="ar")
    
    all_notifications = Column(Boolean, default=True)
    update_alerts = Column(Boolean, default=True)
    new_event_alerts = Column(Boolean, default=True)
    ticket_change_alerts = Column(Boolean, default=True)
    price_change_alerts = Column(Boolean, default=True)
    date_change_alerts = Column(Boolean, default=True)
    location_change_alerts = Column(Boolean, default=True)
    daily_summary = Column(Boolean, default=False)
    
    # Favorites & Filtering
    favorite_categories = Column(JSON, default=list)  # slugs
    favorite_zones = Column(JSON, default=list)       # zone/venue names
    filtered_categories = Column(JSON, default=list)  # excluded slugs
    filtered_zones = Column(JSON, default=list)       # excluded zones
    
    reminder_default_hours = Column(Integer, default=24)
    
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

