import urllib.request
import re

def search_bundle():
    url = "https://wbk-assets.webook.com/0.7.22/assets/index-B-ra0uXs.js"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    with urllib.request.urlopen(req) as resp:
        content = resp.read().decode("utf-8")
        
    print("Bundle length:", len(content))
    endpoints = set(re.findall(r'[\'"`](/api/v2/[^\'"`]+)[\'"`]', content))
    for ep in sorted(endpoints):
        print("API endpoint:", ep)

    search_matches = set(re.findall(r'[\'"`]([^\'"`]*(?:search|discover|events|event|zone|genre)[^\'"`]*)[\'"`]', content))
    filtered = [s for s in search_matches if len(s) < 60 and ("/" in s or "api" in s)]
    for s in sorted(filtered)[:30]:
        print("Candidate path:", s)

if __name__ == "__main__":
    search_bundle()
