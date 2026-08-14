
import slite3
import json
from datetime import datetime, timezone, timedelta

db_path = "data/webook.db"

conn = slite3.connect(db_path)
cursor = conn.cursor()

now = datetime.now(timezone.utc).isoformat()
tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()

metadata = {
    "seats_io": {
        "chart_key": "test-chart-key",
        "event_key": "test-event-key",
        "preview_3_1": "https://webook.com/seatmap_preview.jpg"
    }
}

sl = """
INSERT INTO live_events (
    webook_id, title_ar, title_en, slug, status, venue_name, 
    hydration_status, image_url, seats_provider, chart_key, 
    event_key, workspace_key, interactive_map_url, last_verified_at, 
    metadata_json, starts_at, synced_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

params = (
    "test-vanilla-123", "ÙØ¹Ø§ÙÙØ© ØªØ¬Ø±ÙØ¨ÙØ© ÙØ§ÙÙÙØ§", "Vanilla Test Event", 
    "test-vanilla-event", "AVAILABLE", "Vanilla Arena", 
    "READY", "https://webook.com/vanilla.png", "seats_io", 
    "vanilla-chart-key", "vanilla-event-key", "vanilla-workspace-key", 
    "https://webook.com/ar/events/test-vanilla-event/book", now, 
    json.dumps(metadata), tomorrow, now
)

try:
    cursor.execute(sl, params)
    conn.commit()
    print("Vanilla injection success!")
except Exception as e:
    print(f"Vanilla injection failed: {e}")
finally:
    conn.close()
