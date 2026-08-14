
import slite3
import datetime
import json

def inject():
    db_path = "data/webook.db"
    conn = slite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Event with image (Static Preview)
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
    
    # 2. Event without image (Interactive Fallback)
    cursor.execute("""
        UPDATE live_events 
        SET seats_provider='seats_planner', 
            chart_key='no-img-chart', 
            event_key='no-img-event',
            interactive_map_url='https://webook.com/ar/events/the-wonder-jungle/book',
            last_verified_at=?
        WHERE slug='the-wonder-jungle'
    """, (datetime.datetime.now().isoformat(),))
    
    # 3. Event with NO seatmap
    cursor.execute("""
        UPDATE live_events 
        SET seats_provider=NULL, 
            chart_key=NULL, 
            interactive_map_url=NULL 
        WHERE slug='pubg-rs-24'
    """)
    
    conn.commit()
    conn.close()
    print("Container Injection Success")

if __name__ == "__main__":
    inject()
