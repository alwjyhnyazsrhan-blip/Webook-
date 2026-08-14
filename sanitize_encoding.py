import os

def sanitize_file(path):
    try:
        with open(path, 'rb') as f:
            content = f.read()
        
        # Try to decode as utf-8, if fails, it might be mangled
        try:
            text = content.decode('utf-8')
        except UnicodeDecodeError:
            # If it's mangled latin-1, try to fix it
            text = content.decode('latin-1')
        
        # Write back as clean UTF-8
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(text)
        print(f"Sanitized {path}")
    except Exception as e:
        print(f"Failed to sanitize {path}: {e}")

files_to_fix = [
    r"c:\Users\batoot\Downloads\webook_FIXED_v7\webook_v6\apps\bot\handlers.py",
    r"c:\Users\batoot\Downloads\webook_FIXED_v7\webook_v6\apps\bot\handlers_sub.py",
    r"c:\Users\batoot\Downloads\webook_FIXED_v7\webook_v6\apps\bot\main.py",
    r"c:\Users\batoot\Downloads\webook_FIXED_v7\webook_v6\core\i18n.py"
]

for p in files_to_fix:
    sanitize_file(p)
