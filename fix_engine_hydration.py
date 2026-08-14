import sys

with open("services/discovery/engine.py", "r", encoding="utf-8") as f:
    content = f.read()

old_hydration_block = """            event.interactive_map_url = f"https://webook.com/ar/events/{event.slug}"
            event.last_verified_at = datetime.now(timezone.utc)

            event.metadata_json = data
            event.hydration_status = "READY"
            event.hydrated_at = datetime.now(timezone.utc)
            event.last_hydration_error = None"""

new_hydration_block = """            event.interactive_map_url = f"https://webook.com/ar/events/{event.slug}"
            event.last_verified_at = datetime.now(timezone.utc)
            
            # Accurate Event Scheduling
            start_ts = data.get("start_date_time") or data.get("startDate")
            if start_ts:
                try:
                    event.starts_at = datetime.fromtimestamp(int(start_ts), tz=timezone.utc)
                except Exception:
                    pass
            
            # Accurate Status Handling
            is_soldout = data.get("is_soldout") or data.get("is_sold_out") or data.get("sold_out")
            tickets = data.get("event_tickets") or data.get("ticket_packages") or []
            
            if is_soldout or (data.get("status") == "past") or (not tickets and data.get("status") != "upcoming"):
                event.status = "SOLD_OUT"
            else:
                event.status = "AVAILABLE"

            event.metadata_json = data
            event.hydration_status = "READY"
            event.hydrated_at = datetime.now(timezone.utc)
            event.last_hydration_error = None"""

if old_hydration_block in content:
    content = content.replace(old_hydration_block, new_hydration_block)
    print("Successfully updated hydration logic")
else:
    print("Could not find old_hydration_block")

with open("services/discovery/engine.py", "w", encoding="utf-8") as f:
    f.write(content)
