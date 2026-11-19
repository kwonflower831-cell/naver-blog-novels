import urllib.request
import re

url = "https://blog.naver.com/PostView.naver?blogId=kwonflower58&logNo=224483068656"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req) as resp:
    html = resp.read().decode("utf-8")

m = re.search(r"<title>(.*?)</title>", html)
print("Title:", m.group(1) if m else "No title")

paras = re.findall(r'<p class="se-text-paragraph[^>]*>(.*?)</p>', html, re.DOTALL)
print("Paragraphs found:", len(paras))
for i, p in enumerate(paras[:5]):
    clean = re.sub(r'<[^>]+>', '', p).strip()
    print(f"[{i}] {clean}")
