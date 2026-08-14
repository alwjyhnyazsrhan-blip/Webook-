from datetime import datetime, timezone
from database.repositories.account import AccountRepository
from database.models.account import AuthSession, AccountRole, AccountHealth
from modules.webook.client import WebookApiClient
from modules.auth.fingerprint import FingerprintGenerator
from core.logging.logger import logger
from sqlalchemy import select
import json


class AccountManager:
    """
    Production Account Pool Orchestrator.
    Manages token lifecycle, session validation, fingerprint rotation,
    and pool distribution across SNIPER / EXTENSION / MONITOR roles.
    """

    def __init__(self, db_session):
        self.db = db_session
        self.repo = AccountRepository(db_session)

    # â•â•â• ACCOUNT REGISTRATION â•â•â•

    async def add_account_via_token(self, bearer_token: str, role: str = AccountRole.SNIPER.value) -> dict:
        """
        Register an account by verifying its bearer token against Webook API.
        Returns profile data on success, error dict on failure.
        """
        client = WebookApiClient(bearer_token=bearer_token)
        profile = await client.get_user_profile()

        if not profile or not profile.get("email"):
            return {"error": "Token invalid or expired"}

        # Generate unique fingerprint for this account
        fp = FingerprintGenerator.generate()

        email = profile.get("email", "")
        # Check if account already exists
        from sqlalchemy import select
        stmt = select(AuthSession).where(AuthSession.email == email)
        existing = (await self.db.execute(stmt)).scalar_one_or_none()

        if existing:
            # Update token for existing account
            existing.bearer_token = bearer_token
            existing.health = AccountHealth.ACTIVE.value
            existing.is_active = True
            existing.first_name = profile.get("first_name", "")
            existing.last_name = profile.get("last_name", "")
            existing.user_agent = fp.get("User-Agent", "")
            existing.fingerprint_json = json.dumps(fp)
            await self.db.commit()
            return {"status": "updated", "email": email, "profile": profile}

        # Create new account
        session = AuthSession(
            email=email,
            phone=profile.get("mobile", ""),
            first_name=profile.get("first_name", ""),
            last_name=profile.get("last_name", ""),
            bearer_token=bearer_token,
            device_token="telegram",
            role=role,
            health=AccountHealth.ACTIVE.value,
            is_active=True,
            user_agent=fp.get("User-Agent", ""),
            fingerprint_json=json.dumps(fp),
        )
        self.db.add(session)
        await self.db.commit()

        return {"status": "created", "email": email, "profile": profile}

    # â•â•â• TOKEN LIFECYCLE â•â•â•

    async def verify_account(self, account_id: int) -> bool:
        """Live session verification against Webook API with proactive refresh."""
        account = await self.db.get(AuthSession, account_id)
        if not account:
            return False

        # 1. Proactive Expiry Detection (JWT Decode)
        try:
            token = account.bearer_token
            if token and "." in token:
                import base64
                import json
                # JWT structure: header.payload.signature
                parts = token.split(".")
                if len(parts) >= 2:
                    # Pad the payload for base64 decoding
                    payload_b64 = parts[1]
                    padding = "=" * (4 - len(payload_b64) % 4)
                    payload_json = base64.b64decode(payload_b64 + padding).decode("utf-8")
                    payload = json.loads(payload_json)
                    exp = payload.get("exp")
                    if exp:
                        now_ts = datetime.now(timezone.utc).timestamp()
                        # If expires in less than 30 minutes, try refresh
                        if (exp - now_ts) < 1800:
                            logger.info(f"AccountManager: Token for {account.email} expiring soon (in {int(exp - now_ts)}s). Triggering refresh...")
                            if account.refresh_token:
                                client = WebookApiClient(bearer_token=token)
                                refreshed = await client.refresh_token(account.refresh_token)
                                if refreshed.get("access_token"):
                                    await self.repo.update_token(
                                        account_id,
                                        refreshed["access_token"],
                                        refreshed.get("refresh_token")
                                    )
                                    return True
        except Exception as e:
            logger.warning(f"AccountManager: JWT decode failed for {account_id}: {e}")

        # 2. Live Verification
        client = WebookApiClient(bearer_token=account.bearer_token)
        profile = await client.get_user_profile()

        if profile and profile.get("email"):
            account.health = AccountHealth.ACTIVE.value
            account.is_active = True
            account.last_used_at = datetime.now(timezone.utc)
            await self.db.commit()
            return True
        else:
            # Mark expired
            await self.repo.invalidate_session(account_id)
            return False

    async def verify_all_accounts(self) -> dict:
        """Batch verify every stored account that still has a bearer token."""
        stmt = select(AuthSession).where(AuthSession.bearer_token.isnot(None))
        accounts = (await self.db.execute(stmt)).scalars().all()
        results = {"active": 0, "expired": 0, "total": len(accounts)}
        for acc in accounts:
            ok = await self.verify_account(acc.id)
            if ok:
                results["active"] += 1
            else:
                results["expired"] += 1
        return results

    # â•â•â• POOL MANAGEMENT â•â•â•

    async def get_sniper_for_event(self, event_slug: str) -> AuthSession:
        """Get the best available sniper account for an event."""
        account = await self.repo.get_sniper_account()
        if not account:
            # Fallback to any available account
            account = await self.repo.get_healthy_account()
        return account

    async def get_extension_for_swap(self, current_account_id: int) -> AuthSession:
        """Get an extension account for hold-token swap."""
        return await self.repo.get_extension_account(exclude_id=current_account_id)

    async def get_pool_summary(self) -> dict:
        """Dashboard-ready pool summary."""
        all_accounts = await self.repo.get_available_accounts()
        holding = await self.repo.get_accounts_with_active_holds()
        sniper_accounts = [a for a in all_accounts if a.role == AccountRole.SNIPER.value]
        extension_accounts = [a for a in all_accounts if a.role == AccountRole.EXTENSION.value]
        monitor_accounts = [a for a in all_accounts if a.role == AccountRole.MONITOR.value]

        return {
            "total": len(all_accounts),
            "sniper": len(sniper_accounts),
            "extension": len(extension_accounts),
            "monitor": len(monitor_accounts),
            "holding": len(holding),
            "accounts": all_accounts,
            "holding_accounts": holding,
        }

