import re

file_path = 'apps/bot/handlers.py'
with open(file_path, 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        # Look for a line containing an f-string start
        if 'f"' in line or "f'" in line:
            # Find all content between { and }
            matches = re.findall(r'\{(.*?)\}', line)
            for m in matches:
                if '\\' in m:
                    print(f"Line {i+1}: {line.strip()}")
                    break
