from sqlalchemy import Column, BigInteger, Integer, String, DateTime, ForeignKey, JSON, Boolean
from database.models.base import Base
from datetime import datetime, timezone
import enum


class TaskStatus(enum.Enum):
    CREATED       = "CREATED"
    AUTH_REQUIRED = "AUTH_REQUIRED"
    QUEUED        = "QUEUED"
    PROCESSING    = "PROCESSING"
    SEARCHING     = "SEARCHING"
    RUNNING       = "RUNNING"
    HOLDING       = "HOLDING"
    RESERVED      = "RESERVED"
    SUCCESS       = "SUCCESS"
    COMPLETED     = "COMPLETED"
    FAILED        = "FAILED"
    RETRYING      = "RETRYING"
    EXPIRED       = "EXPIRED"
    CANCELLED     = "CANCELLED"


# Status contract helpers
VALID_TASK_STATUSES: frozenset = frozenset(s.value for s in TaskStatus)

TERMINAL_TASK_STATUSES: frozenset = frozenset({
    TaskStatus.COMPLETED.value, TaskStatus.FAILED.value,
    TaskStatus.CANCELLED.value, TaskStatus.EXPIRED.value,
    TaskStatus.SUCCESS.value,
})

ACTIVE_TASK_STATUSES: frozenset = frozenset({
    TaskStatus.QUEUED.value, TaskStatus.SEARCHING.value,
    TaskStatus.RETRYING.value, TaskStatus.PROCESSING.value,
    TaskStatus.RUNNING.value, TaskStatus.HOLDING.value,
})


def normalize_status(raw: str) -> str:
    """
    Coerce any status string to canonical UPPERCASE form.
    Raises ValueError for unknown statuses.
    Single gate for all status normalization â€” never write raw lowercase to task.status.
    """
    if raw is None:
        raise ValueError("task status is None")
    normalized = raw.strip().upper()
    if normalized not in VALID_TASK_STATUSES:
        raise ValueError(
            f"Unknown task status: '{raw}' (normalized='{normalized}'). "
            f"Valid: {sorted(VALID_TASK_STATUSES)}"
        )
    return normalized


from sqlalchemy import event

# ── INVARIANT ASSERTION ENGINE ──
@event.listens_for(Base, 'before_update', propagate=True)
def enforce_terminal_state_invariant(mapper, connection, target):
    if not isinstance(target, ReservationTask):
        return
        
    # Prevent mutations after reaching a terminal state
    # SQLAlchemy's instance_state keeps track of the previous values
    from sqlalchemy.orm import attributes
    history = attributes.get_history(target, 'status')
    
    if history.has_changes():
        old_status = history.deleted[0] if history.deleted else None
        new_status = history.added[0] if history.added else None
        
        # If the OLD status was terminal, reject the change
        if old_status in TERMINAL_TASK_STATUSES and old_status != new_status:
            # The only exception is if Reconciliation is rescuing a FAILED state into COMPLETED
            if old_status in ("FAILED", "FAILED_DLQ") and new_status in ("COMPLETED", "SUCCESS"):
                pass # Allow retroactive success via reconciliation
            else:
                raise ValueError(f"[INVARIANT_VIOLATION] Cannot mutate task from terminal state {old_status} to {new_status}")

class ReservationTask(Base):
    __tablename__ = "reservation_tasks"

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, index=True)
    account_id = Column(Integer, ForeignKey("auth_sessions.id"), nullable=True)

    # Target Data (Immutable once queued)
    event_slug = Column(String, nullable=False)
    event_id = Column(String, nullable=True)
    category = Column(String, nullable=True) # Human-readable category/ticket label. Legacy rows may still hold a raw ticket id.
    timeslot_id = Column(String, nullable=True)
    team_id = Column(String, nullable=True)
    zone = Column(String, nullable=True) # E.g. "Block A"
    seat_count = Column(Integer, default=1)

    # State Machine & Orchestration
    status = Column(String, default=TaskStatus.CREATED.value, index=True)
    worker_id = Column(String, nullable=True)   # UUID of the worker owning the task
    last_heartbeat = Column(DateTime(timezone=True), nullable=True)  # For failover detection
    
    # Distributed Safety & Transactional Identity
    operation_uuid = Column(String, unique=True, nullable=True)  # Global Idempotency Key
    fencing_token = Column(Integer, default=0)                   # Monotonic lease version

    # Hold & Success Data
    hold_token = Column(String, nullable=True)
    reservation_id = Column(String, nullable=True)
    hold_expires_at = Column(DateTime(timezone=True), nullable=True)

    # Resilience & Telemetry
    retry_count = Column(Integer, default=0)
    error_message = Column(String, nullable=True)
    # Sniper mode: skip all human simulation delays for maximum speed
    sniper_mode = Column(Boolean, default=False)
    trace_id = Column(String, nullable=True)  # Links task execution to origin UI trace
    root_trace_id = Column(String, nullable=True)
    depth = Column(Integer, default=0)

    execution_logs = Column(JSON, default=list)  # Full trace [timestamp, state, msg]
    reserved_seats = Column(JSON, nullable=True) # Detailed seat objects for swap precision

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def get_selection_context(self) -> dict:
        logs = self.execution_logs or []
        if not isinstance(logs, list):
            return {}
        for entry in reversed(logs):
            if isinstance(entry, dict) and isinstance(entry.get("selection_context"), dict):
                return entry["selection_context"]
        return {}
