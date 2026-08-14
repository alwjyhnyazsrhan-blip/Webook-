import os
import re

# Mapping of common mangled sequences back to clean UTF-8
MOJIBAKE_MAP = {
    "\U0001f3af": "\U0001f3af",
    "\U0001f4e1": "\U0001f4e1",
    "\U0001f4cd": "\U0001f4cd",
    "â°": "â°",
    "\U0001f3ad": "\U0001f3ad",
    "\U0001f3ab": "\U0001f3ab",
    "\U0001f7e2": "\U0001f7e2",
    "\U0001f534": "\U0001f534",
    "\U0001f680": "\U0001f680",
    "\U0001f464": "\U0001f464",
    "\u2699ï¸": "\u2699ï¸",
    "\U0001f517": "\U0001f517",
    "\U0001f4cb": "\U0001f4cb",
    "\U0001f39f": "\U0001f39f",
    "\U0001f515": "\U0001f515",
    "\U0001f4cc": "\U0001f4cc",
    "\u0641\u0639\u0627\u0644\u064a\u0627\u062a": "\u0641\u0639\u0627\u0644\u064a\u0627\u062a",
    "\u0627\u0644\u064a\u0648\u0645": "\u0627\u0644\u064a\u0648\u0645",
    "\u0627\u062e\u062a\u0631": "\u0627\u062e\u062a\u0631",
    "\u0627\u0644\u062a\u0635\u0646\u064a\u0641": "\u0627\u0644\u062a\u0635\u0646\u064a\u0641",
    "\u062c\u0645\u064a\u0639": "\u062c\u0645\u064a\u0639",
    "\u0627\u0644\u0628\u064a\u0627\u0646\u0627\u062a": "\u0627\u0644\u0628\u064a\u0627\u0646\u0627\u062a",
    "\u0645\u0632\u0627\u0645\u0646\u0629": "\u0645\u0632\u0627\u0645\u0646\u0629",
    "\u062a\u062d\u062f\u064a\u062b": "\u062a\u062d\u062f\u064a\u062b",
    "\u0639\u0648\u062f\u0629": "\u0639\u0648\u062f\u0629",
}

def deep_sanitize(path):
    try:
        # Read the file as bytes first
        with open(path, 'rb') as f:
            raw_content = f.read()
        
        # Try to decode as utf-8. If it's mangled, it will still decode but look like garbage.
        text = raw_content.decode('utf-8', errors='ignore')
        
        # Replace known mangled patterns
        # Note: This is a bit of a heuristic, but necessary because previous "fixes" 
        # likely saved the mangled characters as valid UTF-8.
        original_text = text
        for mangled, fixed in MOJIBAKE_MAP.items():
            text = text.replace(mangled, fixed)
        
        # Also handle the line dividers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€...
        text = re.sub(r'â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€+', 'â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€', text)
        
        # If we made changes, save it
        if text != original_text:
            with open(path, 'w', encoding='utf-8', newline='\n') as f:
                f.write(text)
            print(f"Deep Sanitized: {path}")
        else:
            # Check if it was double-encoded as Latin-1
            try:
                # If we take the bytes and decode as latin-1, then re-encode as utf-8
                # some people's "fix" scripts do this.
                test_fix = raw_content.decode('utf-8').encode('latin-1').decode('utf-8')
                if test_fix != text:
                    with open(path, 'w', encoding='utf-8', newline='\n') as f:
                        f.write(test_fix)
                    print(f"Restored Encoding: {path}")
            except:
                pass
    except Exception as e:
        print(f"Error sanitizing {path}: {e}")

files = [
    r"c:\Users\batoot\Downloads\webook_FIXED_v7\webook_v6\apps\bot\handlers.py",
    r"c:\Users\batoot\Downloads\webook_FIXED_v7\webook_v6\apps\bot\handlers_sub.py",
    r"c:\Users\batoot\Downloads\webook_FIXED_v7\webook_v6\apps\bot\main.py",
    r"c:\Users\batoot\Downloads\webook_FIXED_v7\webook_v6\core\i18n.py"
]

for f in files:
    deep_sanitize(f)
