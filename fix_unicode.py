import os
import re

count = 0
for root, _, files in os.walk('.'):
    for f in files:
        if f.endswith('.py') and f != 'fix_unicode.py':
            path = os.path.join(root, f)
            try:
                with open(path, 'r', encoding='utf-8') as file:
                    content = file.read()
                
                new_content = re.sub(r'\\u1f([0-9a-fA-F]{2})', r'\\U0001f\1', content)
                
                if content != new_content:
                    with open(path, 'w', encoding='utf-8') as file:
                        file.write(new_content)
                    print(f'Fixed {path}')
                    count += 1
            except Exception as e:
                pass
print(f'Total files fixed: {count}')
