from sqlalchemy import select, update, func
from database.repositories.base import BaseRepository
from database.models.account import AuthSession, AccountRole, AccountHealth
from datetime import datetime, timezone


class AccountRepository(BaseRepository[AuthSession]):
    def __init__(self, session):
        super().__init__(AuthSession, session)

    # â•â•â• POOL QUERIES â•â•â•

    async def get_healthy_account(self, role: str = None) -> AuthSession:
        """
        Get a healthy account, prioritizing those with Residential Proxies.
        Mandated by project pillars for session independence.
        """
        stmt = select(self.model).where(
            self.model.is_active == True,
            self.model.health == AccountHealth.ACTIVE.value,
        )
        if role:
            stmt = stmt.where(self.model.role == role)
        
        # PILLAR ENFORCEMENT: Prioritize accounts with proxies (NOT NULL first)
        # and then use least-recently-used to distribute load.
        stmt = stmt.order_by(
            self.model.proxy_url.desc().nulls_last(), # Proxied accounts first
            self.model.last_used_at.asc().nullsfirst()
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_sniper_account(self) -> AuthSession:
        """Get an available sniper account."""
        return await self.get_healthy_account(role=AccountRole.SNIPER.value)

    async def get_extension_account(self, exclude_id: int = None) -> AuthSession:
        """Get an available extension account (for hold swaps)."""
        stmt = select(self.model).where(
            self.model.is_active == True,
            self.model.health == AccountHealth.ACTIVE.value,
            self.model.role == AccountRole.EXTENSION.value,
            self.model.current_hold_event == None,  # Not currently holding
        )
        if exclude_id:
            stmt = stmt.where(self.model.id != exclude_id)
        stmt = stmt.order_by(self.model.last_used_at.asc().nullsfirst())
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_available_accounts(self):
        """All active and healthy accounts for UI listing."""
        stmt = select(self.model).where(
            self.model.is_active == True,
            self.model.health == AccountHealth.ACTIVE.value
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_accounts_by_role(self, role: str):
        """Get accounts filtered by role."""
        stmt = select(self.model).where(
            self.model.is_active == True,
            self.model.role == role
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_accounts_with_active_holds(self):
        """Get accounts that currently hold tickets."""
        now = datetime.now(timezone.utc)
        stmt = select(self.model).where(
            self.model.current_hold_event != None,
            self.model.hold_expires_at > now,
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    # â•â•â• STATE UPDATES â•â•â•

    async def mark_holding(self, account_id: int, event_slug: str, expires_at: datetime):
        """Mark an account as currently holding tickets for an event."""
        stmt = update(self.model).where(self.model.id == account_id).values(
            current_hold_event=event_slug,
            hold_expires_at=expires_at,
            last_used_at=datetime.now(timezone.utc),
        )
        await self.session.execute(stmt)

    async def clear_hold(self, account_id: int):
        """Clear hold state after swap or release."""
        stmt = update(self.model).where(self.model.id == account_id).values(
            current_hold_event=None,
            hold_expires_at=None,
        )
        await self.session.execute(stmt)

    async def set_role(self, account_id: int, role: str):
        """Change account pool role."""
        stmt = update(self.model).where(self.model.id == account_id).values(role=role)
        await self.session.execute(stmt)
        await self.session.commit()

    async def invalidate_session(self, account_id: int):
        stmt = update(self.model).where(self.model.id == account_id).values(
            is_active=False, health=AccountHealth.EXPIRED.value
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def ban_account(self, account_id: int):
        stmt = update(self.model).where(self.model.id == account_id).values(
            health=AccountHealth.BANNED.value, is_active=False
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def update_usage(self, account_id: int, success: bool = True, error: str = None):
        """Update usage stats and calculate success rate."""
        stmt = select(self.model).where(self.model.id == account_id)
        acc = (await self.session.execute(stmt)).scalar_one_or_none()
        if not acc: return

        acc.last_used_at = datetime.now(timezone.utc)
        if success:
            acc.total_bookings += 1
        else:
            acc.failed_attempts += 1
            acc.last_error = error

        # Recalculate success rate (0-100)
        total = acc.total_bookings + acc.failed_attempts
        if total > 0:
            acc.success_rate = int((acc.total_bookings / total) * 100)
        
        await self.session.commit()

    async def increment_bookings(self, account_id: int):
        await self.update_usage(account_id, success=True)

    async def update_token(self, account_id: int, new_token: str, refresh: str = None):
        """Update bearer token after refresh."""
        vals = {"bearer_token": new_token, "health": AccountHealth.ACTIVE.value}
        if refresh:
            vals["refresh_token"] = refresh
        stmt = update(self.model).where(self.model.id == account_id).values(**vals)
        await self.session.execute(stmt)
        await self.session.commit()

    # â•â•â• STATS â•â•â•

    async def get_pool_stats(self) -> dict:
        """Return account pool statistics for dashboard."""
        stmt = select(
            self.model.role,
            self.model.health,
            func.count(self.model.id)
        ).group_by(self.model.role, self.model.health)
        result = await self.session.execute(stmt)
        stats = {}
        for role, health, count in result:
            stats[f"{role}_{health}"] = count
        return stats

