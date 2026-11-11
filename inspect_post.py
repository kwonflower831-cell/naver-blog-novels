import urllib.request, re

url = "https://blog.naver.com/PostView.naver?blogId=kwonflower58&logNo=224473018625&redirect=Dlog&widgetTypeCall=true&directAccess=false"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
txt = urllib.request.urlopen(req).read().decode("utf-8", errors="replace")

title_m = re.findall(r'<title>([\s\S]*?)</title>', txt)
paras = re.findall(r'<p class="se-text-paragraph[^"]*">([\s\S]*?)</p>', txt)

def clean(s):
    s = re.sub(r'<[^>]+>', '', s)
    return s.strip()

print("Title:", title_m[0] if title_m else "")
print("Total paragraphs:", len(paras))
for i, p in enumerate(paras[:5]):
    print(f"P{i}: {clean(p)}")
if paras:
    print(f"Last P: {clean(paras[-1])}")
