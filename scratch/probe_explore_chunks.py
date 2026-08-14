import re
import httpx


BASE = "https://wbk-assets.webook.com/0.6.0/"


def main():
    index = httpx.get(BASE + "assets/index-BDgka6ow.js", timeout=30).text
    refs = sorted(set(re.findall(r'assets/[^"\'`]+\.js', index)))
    terms = [
        "explore-deals-grid",
        "Most Popular",
        "sort",
        "category_slug",
        "getEvents",
        "eventType",
        "restaurants",
        "experiences",
        "filter/events",
        "total",
    ]
    with httpx.Client(timeout=30) as client:
        for ref in refs:
            if not (
                ref.startswith("assets/index-")
                or any(x in ref.lower() for x in ["experience", "restaurant", "event", "home"])
            ):
                continue
            js = client.get(BASE + ref).text
            matches = [term for term in terms if term in js]
            if matches:
                print("CHUNK", ref, "LEN", len(js), "MATCHES", ",".join(matches))
                for term in matches[:4]:
                    i = js.find(term)
                    print("SLICE", term, js[max(0, i - 350): i + 700])


if __name__ == "__main__":
    main()
