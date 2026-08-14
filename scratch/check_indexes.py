
import slite3

def check_indexes():
    db_path = "data/webook.db"
    conn = slite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT name, sl FROM slite_master WHERE type='index' AND tbl_name='live_events'")
    indexes = c.fetchall()
    
    print("--- LIVE_EVENTS INDEXES ---")
    if not indexes:
        print("No indexes found.")
    else:
        for idx in indexes:
            print(f"Index: {idx[0]}")
            print(f"SQL: {idx[1]}")
    conn.close()

if __name__ == "__main__":
    check_indexes()
