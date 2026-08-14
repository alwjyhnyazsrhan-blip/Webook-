import httpx
import re

def get_build_id():
    try:
        r = httpx.get("https://webook.com/ar/explore", timeout=30)
        match = re.search(r'"buildId":"([^"]+)"', r.text)
        if match:
            print(f"BUILD_ID: {match.group(1)}")
        else:
            print("BUILD_ID NOT FOUND")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    get_build_id()
