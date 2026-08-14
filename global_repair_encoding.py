import os
import re

# Deep mapping of common mangled sequences
REPAIR_MAP = {
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
    "â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€": "â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€",
}

def repair_file(file_path):
    try:
        with open(file_path, 'rb') as f:
            data = f.read()
        
        # Try to decode safely
        try:
            text = data.decode('utf-8')
        except UnicodeDecodeError:
            text = data.decode('latin-1', errors='ignore')
        
        original_text = text
        for mangled, fixed in REPAIR_MAP.items():
            text = text.replace(mangled, fixed)
        
        # Fix long dividers
        text = re.sub(r'â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€+', 'â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€', text)
        
        if text != original_text:
            with open(file_path, 'w', encoding='utf-8', newline='\n') as f:
                f.write(text)
            print(f"REPAIRED: {file_path}")
            return True
    except Exception as e:
        print(f"ERROR {file_path}: {e}")
    return False

def global_fix(root_dir):
    repaired_count = 0
    for root, dirs, files in os.walk(root_dir):
        if '.gemini' in root or '__pycache__' in root or '.git' in root:
            continue
        for file in files:
            if file.endswith('.py') or file.endswith('.json') or file.endswith('.env'):
                if repair_file(os.path.join(root, file)):
                    repaired_count += 1
    print(f"Global repair finished. Total files repaired: {repaired_count}")

if __name__ == "__main__":
    global_fix(".")
