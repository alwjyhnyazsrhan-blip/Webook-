import os

file_path = 'services/reservation/worker.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace escaped quotes
content = content.replace('\\"', '"')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Cleanup completed.")
