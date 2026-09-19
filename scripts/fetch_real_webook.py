import urllib.request
import re
import json

def fetch_webook_homepage():
    urls = [
        "https://webook.com/ar",
        "https://webook.com/en",
        "https://webook.com/ar/explore",
        "https://webook.com/ar/experiences",
    ]
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Accept-Language": "ar,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }

    for url in urls:
        print(f"=== Fetching {url} ===")
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                html = resp.read().decode('utf-8', errors='ignore')
                print(f"Length: {len(html)}")
                # Look for JSON-LD structured data or next data or state scripts
                json_lds = re.findall(r'<script type="application/ld\+json">([^<]+)</script>', html)
                print(f"Found {len(json_lds)} JSON-LD scripts")
                for jld in json_lds:
                    try:
                        data = json.loads(jld)
                        print("JSON-LD sample:", json.dumps(data, ensure_ascii=False)[:300])
                    except:
                        pass

                # Look for links with /events/ or /zones/ or /experiences/
                event_links = set(re.findall(r'href="([^"]*/(?:events|zones|experiences)/[^"]*)"', html))
                print(f"Found {len(event_links)} event links:")
                for l in sorted(event_links)[:20]:
                    print("  ", l)

                # Look for titles or text
                titles = re.findall(r'<h[1-4][^>]*>([^<]+)</h[1-4]>', html)
                print(f"Sample headings: {titles[:10]}")
        except Exception as e:
            print(f"Error fetching {url}: {e}")

if __name__ == "__main__":
    fetch_webook_homepage()
