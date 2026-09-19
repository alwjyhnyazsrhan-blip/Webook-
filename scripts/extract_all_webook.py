import urllib.request
import re
import json

def get_all_sitemap_events():
    slugs = []
    for p in range(1, 4):
        u = f"https://webook.com/sitemap_events_{p}.xml"
        try:
            req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            with urllib.request.urlopen(req, timeout=10) as r:
                xml = r.read().decode("utf-8")
                matches = re.findall(r'<loc>https://webook\.com/(?:ar|en)/events/([^/<]+)</loc>', xml)
                for m in matches:
                    s = m.strip()
                    if s and not s.endswith("/book") and s not in slugs:
                        slugs.append(s)
        except Exception as e:
            print(f"Error on page {p}:", e)
            
    print(f"Discovered {len(slugs)} live slugs on Webook.com:")
    print(json.dumps(slugs, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    get_all_sitemap_events()
