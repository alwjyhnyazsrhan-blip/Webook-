import sys
import re

with open("apps/bot/handlers.py", "r", encoding="utf-8") as f:
    content = f.read()

# Collapse multiple newlines (3 or more) into 2
content = re.sub(r'\n{3,}', '\n\n', content)

with open("apps/bot/handlers.py", "w", encoding="utf-8") as f:
    f.write(content)
print("File cleaned up")
