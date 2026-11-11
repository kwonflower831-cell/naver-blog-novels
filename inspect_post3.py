import urllib.request, re

url = "https://blog.naver.com/PostView.naver?blogId=kwonflower58&logNo=224473018625&redirect=Dlog&widgetTypeCall=true&directAccess=false"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
txt = urllib.request.urlopen(req).read().decode("utf-8", errors="replace")

for kw in ["서해진", "가계부", "차 문을 닫는 소리", "10장에 계속"]:
    print(f"'{kw}' in txt?:", kw in txt)

# Look for se-main-container
m = re.search(r'class="se-main-container"([\s\S]*?)</div>\s*</div>\s*<!--', txt)
if m:
    print("Found se-main-container len:", len(m.group(1)))
    p_main = re.findall(r'<p[^>]*>([\s\S]*?)</p>', m.group(1))
    print("p_main count:", len(p_main))
    for i, p in enumerate(p_main[:5]):
        clean = re.sub(r'<[^>]+>', '', p).strip()
        print(f"Main P{i}: {clean}")
    if p_main:
        print("Last Main P:", re.sub(r'<[^>]+>', '', p_main[-1]).strip())
