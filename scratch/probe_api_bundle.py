import re
import httpx


ASSETS = [
    "https://wbk-assets.webook.com/0.6.0/assets/@wbk/api-CeXI483r.js",
    "https://wbk-assets.webook.com/0.6.0/assets/index-BDgka6ow.js",
]


def main():
    with httpx.Client(timeout=30) as client:
        for url in ASSETS:
            js = client.get(url).text
            print("ASSET", url)
            print("LEN", len(js))
            for term in [
                "filter/events",
                "explore",
                "category",
                "categories",
                "search",
                "per_page",
                "visible_in",
                "events",
            ]:
                print("TERM", term, js.find(term))
            pattern = r'(?:api/v2|filter/events|/events|explore|categories|category)[^"\'`\\\s<>{}()]{0,160}'
            hits = sorted(set(m.group(0) for m in re.finditer(pattern, js)))
            print("HITS", len(hits))
            for hit in hits[:160]:
                print("HIT", hit)
            js_assets = sorted(set(re.findall(r'assets/[^"\'`]+\.js', js)))
            print("ASSET_REFS", len(js_assets))
            for asset in js_assets[:250]:
                print("ASSET_REF", asset)


if __name__ == "__main__":
    main()
