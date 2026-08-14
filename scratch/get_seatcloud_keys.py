import re, requests

slug = "rsl-al-shabab-vs-al-ittihad-149965"
url  = f"https://webook.com/ar/events/{slug}"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "ar,en;q=0.9",
}

print(f"Fetching {url}...")
try:
    r = requests.get(url, headers=headers, timeout=15)
    html = r.text

    # UUID pattern: 8-4-4-4-12 hex
    uuids = re.findall(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', html, re.I)
    print("\nUUIDs found in page HTML:")
    for u in sorted(list(set(uuids))):
        print(" ", u)

    # Also grep for seatcloud/seats.io config keys
    for pattern in [r'event[_]?[Kk]ey["\s:]+([a-z0-9\-]+)',
                    r'chart[_]?[Kk]ey["\s:]+([a-z0-9\-]+)',
                    r'workspace[_]?[Kk]ey["\s:]+([a-z0-9\-]+)',
                    r'publicKey["\s:]+([a-z0-9\-]+)']:
        hits = re.findall(pattern, html)
        if hits:
            print(f"\n{pattern[:20]}... → {set(hits)}")
except Exception as e:
    print(f"Error: {e}")
