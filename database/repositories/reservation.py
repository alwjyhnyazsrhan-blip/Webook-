from sqlalchemy import select
from database.repositories.base import BaseRepository
from database.models.reservation import ReservationTask, TaskStatus

class ReservationRepository(BaseRepository[ReservationTask]):
    def __init__(self, session):
        super().__init__(ReservationTask, session)

    async def get_active_tasks(self, user_id: int = None):
        """
        Fetches tasks that are NOT in a terminal state.
        Evidence: Consistent state-aware DB Query.
        """
        from database.models.reservation import TERMINAL_TASK_STATUSES
        stmt = select(self.model).where(self.model.status.notin_(TERMINAL_TASK_STATUSES))
        
        if user_id:
            stmt = stmt.where(self.model.user_id == user_id)
            
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_all_tasks(self, limit=20):
        """Fetches history of tasks for the dashboard."""
        stmt = select(self.model).order_by(self.model.created_at.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

