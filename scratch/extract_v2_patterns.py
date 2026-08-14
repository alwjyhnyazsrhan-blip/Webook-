import re
import os

bundle_path = r'c:\Users\batoot\Downloads\webook_FULL_FIXED_RELEASE\webook_v6\scratch\seatcloud_bundle.js'

with open(bundle_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Look for patterns like /api/v2/...
patterns = [
    r'api/v2/[^"\']+'
]

found = []
for p in patterns:
    found.extend(re.findall(p, content))

for url in sorted(set(found)):
    print(url)
