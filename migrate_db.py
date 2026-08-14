
import sqlite3
import os

db_path = "data/webook.db"

if not os.path.exists(db_path):
    print(f"DB not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

new_columns = [
    ("stadium_map_url", "TEXT"),
    ("eagle_eye_image", "TEXT"),
    ("seat_map_image", "TEXT"),
    ("hydration_status", "TEXT"),
    ("chart_token", "TEXT"),
    ("image_url", "TEXT"),
    ("venue_address", "TEXT"),
    ("min_price", "INTEGER"),
    ("max_price", "INTEGER"),
    ("seats_provider", "TEXT"),
    ("chart_key", "TEXT"),
    ("event_key", "TEXT"),
    ("workspace_key", "TEXT"),
    ("interactive_map_url", "TEXT"),
    ("last_verified_at", "DATETIME"),
    ("metadata_json", "JSON"),
    ("starts_at", "DATETIME"),
    ("synced_at", "DATETIME"),
    ("hydrated_at", "DATETIME"),
    ("hydration_attempts", "INTEGER"),
    ("last_hydration_error", "TEXT")
]

# Get existing columns
cursor.execute("PRAGMA table_info(live_events)")
existing_columns = [row[1] for row in cursor.fetchall()]

for col_name, col_type in new_columns:
    if col_name not in existing_columns:
        print(f"Adding column {col_name} to live_events...")
        try:
            cursor.execute(f"ALTER TABLE live_events ADD COLUMN {col_name} {col_type}")
        except Exception as e:
            print(f"Error adding {col_name}: {e}")
    else:
        print(f"Column {col_name} already exists.")

conn.commit()
conn.close()
print("Migration complete.")
