from typing import Generic, TypeVar, Type, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from database.models.base import Base

T = TypeVar("T", bound=Base)

class BaseRepository(Generic[T]):
    """
    Generic repository providing standard CRUD operations.
    Encapsulates SQLAlchemy logic to keep services clean.
    """
    def __init__(self, model: Type[T], session: AsyncSession):
        self.model = model
        self.session = session

    async def get(self, id: int) -> Optional[T]:
        return await self.session.get(self.model, id)

    async def list(self) -> List[T]:
        result = await self.session.execute(select(self.model))
        return list(result.scalars().all())

    async def create(self, **kwargs) -> T:
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def delete(self, id: int) -> bool:
        stmt = delete(self.model).where(self.model.id == id)
        result = await self.session.execute(stmt)
        return result.rowcount > 0

