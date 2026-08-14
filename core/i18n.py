from typing import Dict, Any
from core.logging.logger import logger

class I18n:
    """
    Production-grade Internationalization System.
    Supports dynamic language switching and RTL.
    """
    _translations: Dict[str, Dict[str, str]] = {
        "ar": {
            "system_active": "\u0646\u0634\u0637 \U0001f7e2",
            "system_standby": "\u0627\u0646\u062a\u0638\u0627\u0631 \U0001f7e1",
            "verified": "\u062a\u0645 \u0627\u0644\u062a\u062d\u0642\u0642",
            "running": "\u0642\u064a\u062f \u0627\u0644\u062a\u0646\u0641\u064a\u0630",
            "dashboard": "\u0644\u0648\u062d\u0629 \u0627\u0644\u062a\u062d\u0643\u0645",
            "sessions": "\u0627\u0644\u062c\u0644\u0633\u0627\u062a",
            "missions": "\u0627\u0644\u0645\u0647\u0627\u0645",
            "start_new_booking": "\U0001f680 [ \u0627\u0628\u062f\u0623 \u062d\u062c\u0632 \u062c\u062f\u064a\u062f ]",
            "all_events": "\U0001f4e1 \u062c\u0645\u064a\u0639 \u0627\u0644\u0641\u0639\u0627\u0644\u064a\u0627\u062a",
            "sync": "\u062a\u062d\u062f\u064a\u062b",
            "monitoring": "\u0627\u0644\u0645\u0631\u0627\u0642\u0628\u0629",
            "accounts": "\U0001f464 \u0627\u0644\u062d\u0633\u0627\u0628\u0627\u062a",
            "settings": "\u2699\ufe0f \u0627\u0644\u0625\u0639\u062f\u0627\u062f\u0627\u062a",
            "link_account": "\U0001f517 \u0631\u0628\u0637 \u062d\u0633\u0627\u0628 Webook",
            "event_details": "\U0001f4cb \u062a\u0641\u0627\u0635\u064a\u0644 \u0627\u0644\u0641\u0639\u0627\u0644\u064a\u0629",
            "book_now": "\U0001f39f \u0627\u062d\u062c\u0632 \u0627\u0644\u0622\u0646",
            "stop_reminder": "\U0001f515 \u0625\u064a\u0642\u0627\u0641 \u0627\u0644\u062a\u0630\u0643\u064a\u0631",
            "no_events_synced": "\U0001f50e \u0644\u0627 \u062a\u0648\u062c\u062f \u0641\u0639\u0627\u0644\u064a\u0627\u062a \u0645\u0634\u0627\u0631\u0643\u0629 \u0628\u0639\u062f. \u0627\u0636\u063a\u0637 \u062a\u062d\u062f\u064a\u062b.",
            "upcoming_event_reminder": "\U0001f4cc \u062a\u0630\u0643\u064a\u0631: \u0641\u0639\u0627\u0644\u064a\u0629 \u0642\u0627\u062f\u0645\u0629!",
            "venue": "\u0627\u0644\u0645\u0643\u0627\u0646",
            "date": "\u0627\u0644\u062a\u0627\u0631\u064a\u062e",
            "time": "\u0627\u0644\u0648\u0642\u062a",
        },
        "en": {
            "system_active": "ACTIVE \U0001f7e2",
            "system_standby": "STANDBY \U0001f7e1",
            "verified": "Verified",
            "running": "Running",
            "dashboard": "Dashboard",
            "sessions": "SESSIONS",
            "missions": "MISSIONS",
            "start_new_booking": "\U0001f680 [ Start New Booking ]",
            "all_events": "\U0001f4e1 All Events",
            "sync": "Sync",
            "monitoring": "Monitoring",
            "accounts": "\U0001f464 Accounts",
            "settings": "\u2699\ufe0f Settings",
            "link_account": "\U0001f517 Link Webook Account",
            "event_details": "\U0001f4cb Event Details",
            "book_now": "\U0001f39f Book Now",
            "stop_reminder": "\U0001f515 Stop Reminder",
            "no_events_synced": "\U0001f50e No events synced yet. Press Sync.",
            "upcoming_event_reminder": "\U0001f4cc Reminder: Upcoming Event!",
            "venue": "Venue",
            "date": "Date",
            "time": "Time",
        }
    }

    @classmethod
    def t(cls, key: str, lang: str = "ar") -> str:
        """Translate a key to the target language."""
        lang_dict = cls._translations.get(lang, cls._translations["ar"])
        return lang_dict.get(key, key)

i18n = I18n()
