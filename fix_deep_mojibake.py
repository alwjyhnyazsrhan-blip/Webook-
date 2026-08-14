import re
import os

def fix_file(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    # Define replacements
    replacements = {
        r"ÃƒÆ’Ã‚Â¯Ãƒâ€šÃ‚Â¸Ãƒâ€šÃ‚Â": "\ufe0f",
        r"ÃƒÆ’Ã‚Â¢Ãƒâ€šÃ‚Â Ãƒâ€šÃ‚Â³": "\U0001f195", # NEW
        r"ÃƒÆ’Ã‚Â¢Ãƒâ€šÃ‚Â Ãƒâ€šÃ‚Â°": "\u23f3",     # Hourglass
        r"ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¢Ãƒâ€šÃ‚Â": "\u2022", # Bullet
        r"ÃƒÂ¢Ã¢â‚¬Â Ã¢â€šÂ¬": "\u2500",            # Dash
        r"Ã¢â€â‚¬": "\u2500",                     # Dash (alternate)
        r"ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¸": "\u00b8",
        r"ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¯": "\u00ef",
        r"Æ’Ã‚Â¢": "\u2500",
        r"Â¬Ã‚Â¢": "\u2500",
        r"€šÃ‚Â": "\u2500",
        r"Æ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¢Ãƒâ€šÃ‚Â": "\u2500",
    }

    # Also fix some long corrupted separators
    content = re.sub(r"(?:──────────────────)?(?:Æ’Ã‚Â¢|Â¬Ã‚Â¢|€šÃ‚Â|ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¢|Ãƒâ€šÃ‚Â){4,}", "──────────────────", content)
    content = re.sub(r"(?:ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¢Ãƒâ€šÃ‚Â\s*){4,}", "──────────────────", content)

    for bad, good in replacements.items():
        content = content.replace(bad, good)

    # Specific fix for the "Control Center" line reported by user
    content = content.replace("⚙\ufe0f مركز التحكم والاعدادات", "⚙\ufe0f <b>مركز التحكم والاعدادات</b>")
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Fixed {path}")

# Target files
files = [
    r"c:\Users\batoot\Downloads\webook_FULL_FIXED_RELEASE\webook_v6\apps\bot\handlers.py",
    r"c:\Users\batoot\Downloads\webook_FULL_FIXED_RELEASE\webook_v6\services\monitor\ghost.py"
]

for p in files:
    if os.path.exists(p):
        fix_file(p)
    else:
        print(f"File not found: {p}")
