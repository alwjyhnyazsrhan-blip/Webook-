import os

FILE_PATH = r"c:\Users\batoot\Downloads\webook bot\apps\bot\handlers.py"

def fix_handlers():
    if not os.path.exists(FILE_PATH):
        print("File not found")
        return

    with open(FILE_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Identify duplicates
    # We want to keep the LATER versions (Hardened ones at the end)
    # And delete the EARLIER ones.
    
    targets = [
        "async def handle_event_detail",
        "async def handle_book_event",
        "async def proceed_to_teams",
        "async def proceed_to_categories"
    ]
    
    # Track the count of each target
    target_counts = {t: 0 for t in targets}
    for line in lines:
        for t in targets:
            if line.strip().startswith(t):
                target_counts[t] += 1
    
    print(f"Target counts: {target_counts}")
    
    new_lines = []
    removed_counts = {t: 0 for t in targets}
    
    i = 0
    while i < len(lines):
        line = lines[i]
        matched = False
        for t in targets:
            if line.strip().startswith(t):
                # If this is the first occurrence and there's a second one, remove this whole function block
                if target_counts[t] > 1 and removed_counts[t] < (target_counts[t] - 1):
                    print(f"Removing duplicate block starting at line {i+1}: {line.strip()}")
                    removed_counts[t] += 1
                    # Skip until next async def or # separator or end of indentation
                    i += 1
                    while i < len(lines):
                        next_line = lines[i]
                        if next_line.strip().startswith("async def") or next_line.strip().startswith("# â•â•â•â•"):
                            break
                        i += 1
                    matched = True
                    break
        
        if not matched:
            new_lines.append(line)
            i += 1

    with open(FILE_PATH, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    print("Cleanup complete")

if __name__ == "__main__":
    fix_handlers()
