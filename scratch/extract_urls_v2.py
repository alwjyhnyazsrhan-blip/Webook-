import re
import os

bundle_path = r'c:\Users\batoot\Downloads\webook_FULL_FIXED_RELEASE\webook_v6\scratch\seatcloud_bundle.js'
output_path = r'c:\Users\batoot\Downloads\webook_FULL_FIXED_RELEASE\webook_v6\scratch\urls_found.txt'

with open(bundle_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Look for patterns like /api/v2/...
patterns = [
    r'https?://api\.seatcloud\.com/[^"\']+',
    r'/api/v\d+/[^"\']+'
]

found = []
for p in patterns:
    found.extend(re.findall(p, content))

with open(output_path, 'w', encoding='utf-8') as f:
    for url in sorted(set(found)):
        f.write(url + '\n')

print(f"Found {len(found)} URLs and wrote them to {output_path}")
