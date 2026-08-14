import os
import re

def fix_file(filepath):
    with open(filepath, 'rb') as f:
        content = f.read()
    
    text = content.decode('utf-8', errors='replace')
    original = text
    
    # Remove control characters
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    
    if text != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"Fixed {filepath}")
    else:
        print(f"No changes needed for {filepath}")

# Fix i18n.py
fix_file(r'C:\Users\batoot\Downloads\webook_bot_fixed\webook_fixed\core\i18n.py')
print("Done!")
