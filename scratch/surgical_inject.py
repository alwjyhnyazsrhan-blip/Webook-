
import slite3
import datetime
import json

db_path = "/app/data/webook.db"
conn = slite3.connect(db_path)
cursor = conn.cursor()

# 1. Ensure columns exist (just in case create_all was weird)
cols = [
    ('seats_provider', 'TEXT'),
    ('chart_key', 'TEXT'),
    ('event_key', 'TEXT'),
    ('workspace_key', 'TEXT'),
    ('interactive_map_url', 'TEXT'),
    ('last_verified_at', 'DATETIME')
]
cursor.execute("PRAGMA table_info(live_events)")
existing = [r[1] for r in cursor.fetchall()]
for col_name, col_type in cols:
    if col_name not in existing:
        cursor.execute(f"ALTER TABLE live_events ADD COLUMN {col_name} {col_type}")

# 2. Inject Case A: Static Image
cursor.execute("""
    UPDATE live_events 
    SET seats_provider='seats_io', 
        chart_key='real-chart-123', 
        event_key='real-event-123', 
        workspace_key='real-ws-123',
        interactive_map_url='https://webook.com/ar/events/rsl-25-26-neom-vs-al-shabab-11052026/book',
        last_verified_at=?,
        metadata_json=?
    WHERE slug='rsl-25-26-neom-vs-al-shabab-11052026'
""", (
    datetime.datetime.now().isoformat(),
    json.dumps({
        "seats_io": {
            "chart_key": "real-chart-123",
            "preview_3_1": "https://images.ctfassets.net/vy53kjs34an/5dFofdnJxuhgJPmtDbddXZ/4dcf6169c8a465da3489fda4f2d90578/1280x426-EN.jpg"
        }
    })
))

# 3. Inject Case B: Interactive Fallback
cursor.execute("""
    UPDATE live_events 
    SET seats_provider='seats_planner', 
        chart_key='no-img-chart', 
        event_key='no-img-event',
        interactive_map_url='https://webook.com/ar/events/the-wonder-jungle/book',
        last_verified_at=?
    WHERE slug='the-wonder-jungle'
""", (datetime.datetime.now().isoformat(),))

# 4. Inject Case C: Unavailable
cursor.execute("""
    UPDATE live_events 
    SET seats_provider=NULL, 
        chart_key=NULL, 
        interactive_map_url=NULL 
    WHERE slug='pubg-rs-24'
""")

conn.commit()
conn.close()
print("Surgical Injection Complete.")
