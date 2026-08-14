import re
import sys

bundle_path = '/app/scratch/seatcloud_bundle.js'

with open(bundle_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Look for patterns like /api/v2/... or https://api.seatcloud.com/...
patterns = [
    r'https?://[a-z0-9.-]*seatcloud\.com[^"\'\s]*',
    r'api/v\d+/[^"\'\s]*'
]

found = []
for p in patterns:
    found.extend(re.findall(p, content))

for url in sorted(set(found)):
    print(url)
