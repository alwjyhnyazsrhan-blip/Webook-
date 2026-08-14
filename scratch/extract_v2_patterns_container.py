import re
import os

bundle_path = '/app/scratch/seatcloud_bundle.js'

if not os.path.exists(bundle_path):
    print(f"File not found: {bundle_path}")
    sys.exit(1)

with open(bundle_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Look for patterns like /api/v2/...
patterns = [
    r'api/v2/[^"\']+',
    r'/api/v\d+/[^"\']+'
]

found = []
for p in patterns:
    found.extend(re.findall(p, content))

for url in sorted(set(found)):
    print(url)
