import os
import re

file_path = r"c:\Users\batoot\Downloads\webook_FULL_FIXED_RELEASE\webook_v6\apps\bot\handlers.py"

with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
    content = f.read()

# 1. Update _MOJIBAKE_MARKERS and _MOJIBAKE_REPLACEMENTS
markers_block = """_MOJIBAKE_MARKERS = ("Ã", "Â", "â", "ï", "", "Æ", "€")
_MOJIBAKE_REPLACEMENTS = {
    "ÃƒÆ’Ã‚Â¯Ãƒâ€šÃ‚Â¸Ãƒâ€šÃ‚Â": "\\\\ufe0f",
    "ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¯ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¸ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â": "\\\\ufe0f",
    "ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¢Ãƒâ€šÃ‚Â": "•",
    "ÃƒÆ’Ã‚Â¢Ãƒâ€šÃ‚Â Ãƒâ€šÃ‚Â³": "🆕",
    "ÃƒÆ’Ã‚Â¢Ãƒâ€šÃ‚Â Ãƒâ€šÃ‚Â°": "⏳",
    "ÃƒÆ’Ã‚Â¢Ãƒâ€šÃ‚Â Ãƒâ€šÃ‚Â»": "»",
    "ÃƒÆ’Ã‚Â¢Ãƒâ€šÃ‚Â¬Ãƒâ€šÃ‚Â¢": "•",
    "ÃƒÆ’Ã‚Â¯Ãƒâ€šÃ‚Â¿Ãƒâ€šÃ‚Â½": "",
    "Ãƒâ€šÃ‚Â ": " ",
    "Ã‚Â ": " ",
    "Æ’Ã‚Â¢": "",
    "Â¬Ã‚Â¢": "",
    "€šÃ‚Â": "",
}"""

content = re.sub(r'_MOJIBAKE_MARKERS = .*?\}', markers_block, content, flags=re.DOTALL)

# 2. Fix the hardcoded sequences globally in the file
content = content.replace("ÃƒÆ’Ã‚Â¯Ãƒâ€šÃ‚Â¸Ãƒâ€šÃ‚Â", "")
content = content.replace("ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¢Ãƒâ€šÃ‚Â", "•")

# 3. Fix the specific user example sequence
content = content.replace("──────────────────Æ’Ã‚Â¢──────────────────Â¬Ã‚Â¢──────────────────€šÃ‚Â──────────────────Æ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¢Ãƒâ€šÃ‚Â", "──────────────────")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Repair completed.")
