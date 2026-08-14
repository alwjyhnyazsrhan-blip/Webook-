from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from database.models.user_prefs import UserEventSubscription, UserGlobalPrefs
from database.models.discovery import LiveEvent

class UserPrefsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_global_prefs(self, user_id: int) -> UserGlobalPrefs:
        stmt = select(UserGlobalPrefs).where(UserGlobalPrefs.user_id == user_id)
        result = await self.session.execute(stmt)
        prefs = result.scalar_one_or_none()
        if not prefs:
            prefs = UserGlobalPrefs(user_id=user_id)
            self.session.add(prefs)
            await self.session.commit()
        return prefs

    async def update_global_setting(self, user_id: int, field: str, value: any):
        prefs = await self.get_global_prefs(user_id)
        setattr(prefs, field, value)
        await self.session.commit()
        return prefs

    async def toggle_list_item(self, user_id: int, field: str, item: str):
        """Toggle an item in a JSON list (e.g., favorite_categories)"""
        prefs = await self.get_global_prefs(user_id)
        current_list = list(getattr(prefs, field) or [])
        if item in current_list:
            current_list.remove(item)
        else:
            current_list.append(item)
        setattr(prefs, field, current_list)
        await self.session.commit()
        return prefs

    async def get_user_subscriptions(self, user_id: int):
        stmt = select(UserEventSubscription).where(UserEventSubscription.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_subscription(self, user_id: int, event_id: int):
        stmt = select(UserEventSubscription).where(
            UserEventSubscription.user_id == user_id,
            UserEventSubscription.event_id == int(event_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def add_subscription(self, user_id: int, event_id: int):
        sub = UserEventSubscription(user_id=user_id, event_id=int(event_id))
        self.session.add(sub)
        await self.session.commit()
        return sub

    async def delete_subscription(self, user_id: int, event_id: int):
        stmt = delete(UserEventSubscription).where(
            UserEventSubscription.user_id == user_id,
            UserEventSubscription.event_id == int(event_id)
        )
        await self.session.execute(stmt)
        await self.session.commit()

