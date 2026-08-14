import os
import re

def to_unicode_escape(match):
    s = match.group(0)
    out = ""
    for c in s:
        code = ord(c)
        if code > 0xFFFF:
            out += f"\\U{code:08x}"
        else:
            out += f"\\u{code:04x}"
    return out

# Regex for Arabic characters and common emojis
# We match ranges that cover most Arabic and Emoticons/Symbols
ARABIC_RE = re.compile(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF\U0001F000-\U0001F9FF\u2600-\u26FF\u2700-\u27BF]+')

def harden_file(path):
    try:
        # Try reading as utf-8
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Fallback to latin-1 (which can read any byte)
            with open(path, 'r', encoding='latin-1') as f:
                content = f.read()
                # If we read it as latin-1, and it contains UTF-8 bytes, 
                # we need to FIX the mojibake.
                try:
                    content = content.encode('latin-1').decode('utf-8')
                except:
                    pass # Keep as is if it's not actually UTF-8
        
        new_content = ARABIC_RE.sub(to_unicode_escape, content)
        
        if new_content != content:
            with open(path, 'w', encoding='utf-8', newline='\n') as f:
                f.write(new_content)
            print(f"HARDENED: {path}")
            return True
    except Exception as e:
        print(f"ERROR {path}: {e}")
    return False

def harden_project(root_dir):
    count = 0
    for root, dirs, files in os.walk(root_dir):
        if '.gemini' in root or '__pycache__' in root or '.git' in root:
            continue
        for file in files:
            if file.endswith('.py'):
                if harden_file(os.path.join(root, file)):
                    count += 1
    print(f"Project hardening finished. Total files hardened: {count}")

if __name__ == "__main__":
    harden_project(".")
