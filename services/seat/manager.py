from modules.webook.client import WebookApiClient
from core.database.postgres import AsyncSessionLocal
from database.models.discovery import LiveEvent
from sqlalchemy import select
from core.logging.logger import logger


def _sanitize_text(text: str) -> str:
    if not isinstance(text, str):
        return str(text) if text is not None else ""
    import unicodedata
    try:
        text = unicodedata.normalize("NFKC", text)
    except Exception:
        pass
    text = text.encode("utf-8", errors="replace").decode("utf-8", errors="replace")
    return text


class SeatManager:
    """
    Real-Time Seat Map & Availability Manager.
    Fetches live data from Webook API — zero hardcoding.
    """

    def __init__(self):
        self.api = WebookApiClient()

    @staticmethod
    def _as_number(value):
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            clean = value.strip().replace(",", "")
            if not clean:
                return None
            try:
                return float(clean)
            except ValueError:
                return None
        return None

    @staticmethod
    def _is_open_status(value) -> bool:
        if value is None:
            return True
        text = str(value).strip().lower()
        if not text:
            return True
        bad = ("sold", "closed", "ended", "expired", "inactive", "paused", "unavailable", "stopped")
        return not any(item in text for item in bad)

    @staticmethod
    def _check_strict_availability(ticket: dict) -> bool:
        is_selectable = ticket.get("isSelectable") or ticket.get("is_selectable")
        is_purchasable = ticket.get("isPurchasable") or ticket.get("is_purchasable")
        sale_enabled = ticket.get("saleEnabled") or ticket.get("sale_enabled")
        offer_locked = ticket.get("offerLocked") or ticket.get("offer_locked")
        on_sale = ticket.get("on_sale") or ticket.get("onSale")
        visibility = ticket.get("visibility")
        access_restricted = ticket.get("accessRestricted") or ticket.get("access_restricted")
        is_hidden = ticket.get("isHidden") or ticket.get("is_hidden")

        if is_hidden in (True, "true", "1"):
            return False
        if access_restricted in (True, "true", "1"):
            return False
        if offer_locked in (True, "true", "1"):
            return False
        if is_selectable in (False, "false", "0"):
            return False
        if is_purchasable in (False, "false", "0"):
            return False
        if sale_enabled in (False, "false", "0"):
            return False
        if on_sale in (False, "false", "0"):
            return False

        return True

    async def get_actual_map_summary(self, event_id: str) -> str:
        """Fetch REAL event detail and generate a live seat availability report."""
        async with AsyncSessionLocal() as db:
            if event_id.isdigit():
                event = await db.get(LiveEvent, int(event_id))
            else:
                stmt = select(LiveEvent).where(LiveEvent.slug == event_id)
                event = (await db.execute(stmt)).scalar_one_or_none()

        if not event:
            return "\u26a0\ufe4f\ufe8f \u0627\u0644\u0625\u062d\u062f\u0627\u062b \u063a\u064a\u0631 \u0645\u062a\u0648\u0641\u0631 \u0641\u064a \u0642\u0627\u0639\u062f\u0629 \u0627\u0644\u0628\u064a\u0627\u0646\u0627\u062a."

        detail = await self.api.get_event_detail(event.slug)
        if not detail:
            return "\u26a0\ufe4f\ufe8f \u062a\u0639\u0630\u0631 \u0627\u0644\u062d\u0635\u0648\u0644 \u0639\u0644\u0649 \u0628\u064a\u0627\u0646\u0627\u062a \u0627\u0644\u062d\u062f\u062b \u0645\u0646 Webook API."

        tickets = detail.get("ticket_packages") or detail.get("event_tickets") or []
        chart_token = detail.get("chart_token") or detail.get("chartToken") or ""
        venue = detail.get("venue", {})
        venue_name = venue.get("name", "") if isinstance(venue, dict) else str(venue)
        home = detail.get("home_team", {})
        away = detail.get("away_team", {})

        report = f"\U0001f4f8 **\u062a\u0642\u0631\u064a\u0631 \u062e\u0637\u0637 \u0627\u0644\u0645\u0642\u0627\u0639\u062f \u0627\u0644\u0645\u062a\u0627\u062d\u0629**\n"
        report += f"\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
        title_val = _sanitize_text(detail.get("title") or event.title_ar or "")
        report += f"\U0001f3ad {title_val}\n"
        venue_val = _sanitize_text(venue_name)
        report += f"\U0001f4cd {venue_val}\n"
        if home and home.get("name"):
            home_val = _sanitize_text(home.get("name", ""))
            away_val = _sanitize_text(away.get("name", ""))
            report += f"\u26bd {home_val} vs {away_val}\n"
        if chart_token:
            report += f"\U0001f5fa\ufe0f\ufe8f Seats.io: `{chart_token[:30]}...`\n"
        report += f"\n"

        if tickets:
            report += f"\U0001f3ab **\u0628\u0648\u0627\u0628\u0627\u062a \u0627\u0644\u062d\u062f\u062b \u0627\u0644\u0645\u062a\u0627\u062d\u0629 ({len(tickets)}):**\n"
            report += f"\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n"
            for t in tickets:
                name_raw = t.get("title") or t.get("name") or "\u2014"
                name = _sanitize_text(name_raw)
                price = t.get("price") or t.get("base_price") or "?"

                remaining = self._as_number(
                    t.get("remaining")
                    or t.get("available")
                    or t.get("available_quantity")
                    or t.get("availableQuantity")
                )
                capacity = self._as_number(
                    t.get("capacity")
                    or t.get("quantity")
                    or t.get("total_quantity")
                    or t.get("totalQuantity")
                )
                sold = self._as_number(
                    t.get("sold_quantity")
                    or t.get("soldQuantity")
                    or t.get("sold")
                )
                sold_out_flag = bool(
                    t.get("sold_out") or t.get("is_sold_out") or t.get("soldOut")
                    or t.get("isSoldOut")
                )
                status_open = self._is_open_status(t.get("status")) and self._is_open_status(t.get("sale_status"))
                strict_available = self._check_strict_availability(t)

                is_available = status_open and not sold_out_flag and strict_available
                if remaining is not None:
                    is_available = is_available and remaining > 0
                elif capacity is not None and sold is not None:
                    is_available = is_available and (capacity - sold) > 0

                status = "\U0001f7e2" if is_available else "\U0001f534"
                cap_text = (
                    str(int(remaining))
                    if remaining is not None
                    else (str(int(capacity)) if capacity is not None else "?")
                )
                sold_text = str(int(sold)) if sold is not None else "?"

                if is_available:
                    report += f"{status} **{name}**\n"
                    report += f"   \U0001f4b0 {price} SAR | \U0001f3ab \u0628\u0627\u0628\u0629: {cap_text} | \u0628\u064a\u0639: {sold_text}\n"
                else:
                    report += f"{status} {name}\n"
                    report += f"   \U0001f4b0 {price} SAR | \U0001f3ab \u0628\u0627\u0628\u0629: {cap_text} | \u0628\u064a\u0639: {sold_text}\n"
        else:
            report += "\u26a0\ufe4f\ufe8f \u0644\u0627 \u062a\u0648\u062c\u062f \u062a\u0630\u0627\u0643\u0631 \u0645\u062a\u0627\u062d\u0629 \u062d\u0627\u0644\u064a\u064b\u0627.\n"

        report += "\n\U0001f4ec \u0644\u0644\u062d\u062c\u0632 \u0627\u0644\u0645\u0628\u0627\u0634\u0631 \u0641\u064a webook.com"
        return report

    async def get_event_full_detail(self, slug: str) -> dict:
        """Get complete event info including tickets, teams, venue, chart."""
        return await self.api.get_event_detail(slug)

    async def get_ticket_categories(self, slug: str) -> list:
        """Get ticket categories with prices and availability."""
        data = await self.api.get_event_tickets(slug)
        return data.get("data", []) if isinstance(data, dict) else []

    async def get_resale_tickets(self, slug: str) -> list:
        """Get resale/secondary market tickets."""
        return await self.api.get_resale_listing(slug)