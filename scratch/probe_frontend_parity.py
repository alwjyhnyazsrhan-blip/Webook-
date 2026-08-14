import re
import httpx


def main():
    url = (
        "https://webook.com/en/explore"
        "?category=restaurants&category=theater&category=sports"
        "&category=experience&category=music"
    )
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;=0.9,ar;=0.8",
    }
    with httpx.Client(timeout=30, follow_redirects=True, headers=headers) as client:
        resp = client.get(url)
    text = resp.text
    print("STATUS", resp.status_code)
    print("FINAL_URL", str(resp.url))
    print("HTML_LEN", len(text))
    print("HAS_NEXT_DATA", "__NEXT_DATA__" in text)
    build = re.search(r'"buildId":"([^"]+)"', text)
    print("BUILD_ID", build.group(1) if build else "")
    chunks = sorted(
        set(
            re.findall(r'/_next/static/[^"\']+\.js', text)
            + re.findall(r'https://wbk-assets\.webook\.com/0\.6\.0/assets/[^"\'<>]+\.js', text)
        )
    )
    print("CHUNK_COUNT", len(chunks))
    for chunk in chunks[:120]:
        print("CHUNK", chunk)
    api_hits = sorted(set(re.findall(r'(?:https://api\.webook\.com|/api/)[^"\'\\\s<]+', text)))
    print("API_HITS", len(api_hits))
    for hit in api_hits[:80]:
        print("API", hit)


if __name__ == "__main__":
    main()
