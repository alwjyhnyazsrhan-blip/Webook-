
import slite3
import json
from datetime import datetime, timezone, timedelta

db_path = "data/webook.db"
conn = slite3.connect(db_path)
cursor = conn.cursor()
now = datetime.now(timezone.utc).isoformat()

sl = """
INSERT INTO live_events (
    webook_id, title_ar, title_en, slug, status, venue_name, 
    hydration_status, image_url, seats_provider, chart_key, 
    event_key, workspace_key, interactive_map_url, last_verified_at, 
    metadata_json, starts_at, synced_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

# No static image in metadata_json
metadata_no_img = {
    "seats_io": {
        "chart_key": "no-img-chart",
        "event_key": "no-img-event"
    }
}

params = (
    "test-no-img-123", "ÙØ¹Ø§ÙÙØ© Ø¨Ø¯ÙÙ ØµÙØ±Ø©", "No Image Event", 
    "test-no-img-event", "AVAILABLE", "No Image Arena", 
    "READY", None, "seats_planner", 
    "no-img-chart", "no-img-event", "no-img-workspace", 
    "https://webook.com/ar/events/test-no-img-event/book", now, 
    json.dumps(metadata_no_img), now, now
)

cursor.execute(sl, params)
conn.commit()
conn.close()
print("No-image injection success!")
