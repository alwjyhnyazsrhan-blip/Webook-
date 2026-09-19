import urllib.request
import re

def inspect_search():
    base = "https://wbk-assets.webook.com/0.7.22/assets/"
    files = ["search-BsEToLDY.js", "search-DkXl1NIQ.js", "search-Dsn_qmU9.js"]
    for f in files:
        url = base + f
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        try:
            with urllib.request.urlopen(req) as resp:
                code = resp.read().decode("utf-8")
                print("====", f, "len:", len(code))
                urls = set(re.findall(r'https?://[a-zA-Z0-9\.\-_/]+', code))
                print("Urls:", urls)
                apis = set(re.findall(r'[\'"`](/api/[^\'"`]+)[\'"`]', code))
                print("API paths:", apis)
                # Look for query, fetch, axios, headers
                snippets = re.findall(r'(?:get|post|request|fetch)\([^\)]+\)', code)
                print("Fetch snippets:", snippets[:5])
        except Exception as e:
            print(f, "->", e)

if __name__ == "__main__":
    inspect_search()
