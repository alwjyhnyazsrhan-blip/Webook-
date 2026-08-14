from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from database.models.base import Base
from datetime import datetime, timezone

class Genre(Base):
    """Dynamic Categories (Sports, Concerts, etc.)"""
    __tablename__ = "genres"
    id = Column(Integer, primary_key=True)
    name_ar = Column(String, nullable=False)
    name_en = Column(String, nullable=False)
    slug = Column(String, unique=True, index=True)
    is_active = Column(Boolean, default=True)

class LiveEvent(Base):
    """Real Synced Events from Webook API v2"""
    __tablename__ = "live_events"
    id = Column(Integer, primary_key=True)
    webook_id = Column(String, unique=True, index=True)
    genre_id = Column(Integer, ForeignKey("genres.id"))
    
    genre = relationship("Genre")

    @property
    def genre_slug(self) -> str:
        return self.genre.slug if self.genre else "all"
    
    title_ar = Column(String, nullable=False)
    title_en = Column(String, nullable=False)
    slug = Column(String, unique=True, index=True)
    status = Column(String, default="AVAILABLE") # AVAILABLE, SOLD_OUT, GHOST
    
    venue_name = Column(String, nullable=True)
    venue_lat = Column(String, nullable=True)
    venue_lng = Column(String, nullable=True)
    stadium_map_url = Column(String, nullable=True)
    eagle_eye_image = Column(String, nullable=True)
    seat_map_image = Column(String, nullable=True)
    
    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    # HYDRATION & METADATA (PHASE 2 HARDENING)
    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    hydration_status = Column(String, default="DISCOVERED") # DISCOVERED, HYDRATING, READY, FAILED, PARTIAL
    chart_token = Column(String, nullable=True) # Deep-extracted seats.io key
    image_url = Column(String, nullable=True) # Full poster resolution
    venue_address = Column(String, nullable=True)
    min_price = Column(Integer, nullable=True)
    max_price = Column(Integer, nullable=True)

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    # SEATMAP METADATA (TASK 3 PERSISTENCE)
    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    seats_provider = Column(String, nullable=True) # e.g., 'seats_planner'
    chart_key = Column(String, nullable=True)
    event_key = Column(String, nullable=True)
    workspace_key = Column(String, nullable=True)
    interactive_map_url = Column(String, nullable=True)
    last_verified_at = Column(DateTime(timezone=True), nullable=True)
    
    metadata_json = Column(JSON, default=dict) # Full API V2 Response Payload
    
    starts_at = Column(DateTime(timezone=True), nullable=True)
    synced_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    hydrated_at = Column(DateTime(timezone=True), nullable=True)
    hydration_attempts = Column(Integer, default=0)
    last_hydration_error = Column(String, nullable=True)

class SeatMapCache(Base):
    """Live Seat Availability Engine Snapshot"""
    __tablename__ = "seat_map_cache"
    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey("live_events.id"))
    
    section_id = Column(String, index=True)
    category_name = Column(String)
    
    total_seats = Column(Integer)
    available_seats = Column(Integer)
    price = Column(Integer)
    
    is_sold_out = Column(Boolean, default=False)
    last_refresh = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
