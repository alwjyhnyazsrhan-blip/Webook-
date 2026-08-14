import os
import re

def scan_dir(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    try:
                        content = f.read()
                        for i, line in enumerate(content.splitlines()):
                            if ('f"' in line or "f'" in line) and '{' in line:
                                matches = re.findall(r'\{(.*?)\}', line)
                                for m in matches:
                                    if '\\' in m:
                                        print(f"{file_path}:{i+1}: {line.strip()}")
                                        break
                    except Exception as e:
                        print(f"Error reading {file_path}: {e}")

print("Scanning apps/bot/...")
scan_dir('apps/bot/')
print("Scanning services/...")
scan_dir('services/')
