
import slite3
import time
import os

def monitor_bookings():
    db_path = "data/webook.db"
    print("--- LIVE BOOKING MONITOR (Task Status) ---")
    print("Watching for new tasks... Press Ctrl+C to stop.")
    
    last_id = 0
    
    while True:
        try:
            conn = slite3.connect(db_path)
            c = conn.cursor()
            
            # Fetch latest 5 tasks
            c.execute("""
                SELECT id, event_slug, status, error_message, reservation_id, created_at 
                FROM reservation_tasks 
                ORDER BY id DESC LIMIT 5
            """)
            tasks = c.fetchall()
            
            if tasks and tasks[0][0] > last_id:
                os.system('cls' if os.name == 'nt' else 'clear')
                print(f"--- LIVE BOOKING MONITOR | Updated: {time.strftime('%H:%M:%S')} ---")
                print(f"{'ID':<5} | {'EVENT':<30} | {'STATUS':<15} | {'RES_ID':<10} | {'ERROR'}")
                print("-" * 80)
                for t in tasks:
                    tid, slug, status, err, res_id, created = t
                    print(f"{tid:<5} | {slug[:30]:<30} | {status:<15} | {str(res_id):<10} | {err or ''}")
                last_id = tasks[0][0]
            
            conn.close()
        except Exception as e:
            print(f"Monitor Error: {e}")
        
        time.sleep(1)

if __name__ == "__main__":
    monitor_bookings()
