# apps/bot/handlers.py
"""
Bot Handler Helpers and Inventory Verification
"""
import os
import sys
from pathlib import Path

_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

def extract_ticket_list(payload):
    """Extracts available tickets from event payload"""
    if isinstance(payload, dict):
        return payload.get("tickets", payload.get("items", []))
    elif isinstance(payload, list):
        return payload
    return []

def ticket_has_available_inventory(ticket):
    """Checks if a ticket has remaining inventory"""
    if not isinstance(ticket, dict):
        return False
    available = ticket.get("available", ticket.get("quantity", ticket.get("remaining", 0)))
    return bool(available and int(available) > 0)

def _seatmap_payload(event_data):
    """Formats seatmap payload for event representation"""
    return {
        "event_id": event_data.get("id") if isinstance(event_data, dict) else str(event_data),
        "status": "ready",
        "zones": ["A", "B", "VIP"]
    }

def extract_detail_fields(event_data):
    """Extracts event detail dictionary"""
    if not isinstance(event_data, dict):
        return {}
    return {
        "title": event_data.get("title", event_data.get("name", "")),
        "venue": event_data.get("venue", event_data.get("location", "")),
        "date": event_data.get("date", ""),
        "price_min": event_data.get("price_min", 0),
    }

def extract_team_options(event_data):
    """Extracts opposing teams or participants"""
    if not isinstance(event_data, dict):
        return []
    return event_data.get("teams", [])
