import urllib.request
import re

req = urllib.request.Request("https://webook.com/ar", headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
with urllib.request.urlopen(req) as resp:
    html = resp.read().decode("utf-8")
    scripts = re.findall(r'src=["\']([^"\']+\.js)["\']', html)
    print("Scripts in homepage HTML:")
    for s in scripts:
        print(s)
