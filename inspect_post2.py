import urllib.request, re

url = "https://blog.naver.com/PostView.naver?blogId=kwonflower58&logNo=224473018625&redirect=Dlog&widgetTypeCall=true&directAccess=false"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
txt = urllib.request.urlopen(req).read().decode("utf-8", errors="replace")

print("se-text matches:", len(re.findall(r'se-text', txt)))
print("se-module matches:", len(re.findall(r'se-module', txt)))
p_all = re.findall(r'<p[^>]*>([\s\S]*?)</p>', txt)
print("p tags count:", len(p_all))
for i, p in enumerate(p_all[:10]):
    clean = re.sub(r'<[^>]+>', '', p).strip()
    if clean:
        print(f"P{i}: {clean[:100]}")
