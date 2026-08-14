import sqlite3

def fix_mojibake(text):
    if not text: return text
    try:
        # If it's mangled, encoding as latin-1 and decoding as utf-8 will fix it.
        return text.encode('latin-1').decode('utf-8')
    except:
        return text

def fix_db():
    conn = sqlite3.connect('data/webook.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, title_ar, slug FROM live_events")
    rows = cursor.fetchall()
    
    updated = 0
    for id, title, slug in rows:
        fixed_title = fix_mojibake(title)
        if fixed_title != title:
            cursor.execute("UPDATE live_events SET title_ar = ? WHERE id = ?", (fixed_title, id))
            updated += 1
            print(f"Fixed title for {slug}: {fixed_title}")
            
    conn.commit()
    conn.close()
    print(f"DB Repair finished. Updated {updated} events.")

if __name__ == "__main__":
    fix_db()
