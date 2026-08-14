import re
import sys

with open(r'c:\Users\batoot\Downloads\webook_FULL_FIXED_RELEASE\webook_v6\scratch\seatcloud_bundle.js', 'r', encoding='utf-8') as f:
    content = f.read()

urls = re.findall(r'https?://api\.seatcloud\.com/[^"\']+', content)
for url in urls:
    print(url)
