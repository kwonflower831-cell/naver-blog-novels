import urllib.request, re

def check_m_post(no):
    url = f'https://m.blog.naver.com/kwonflower58/{no}'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)'})
    txt = urllib.request.urlopen(req).read().decode('utf-8', errors='replace')
    paras = re.findall(r'<p[^>]*class="[^"]*se-text-paragraph[^"]*"[^>]*>([\s\S]*?)</p>', txt)
    print(f'Post {no}: mobile paras={len(paras)}')
    for p in paras[:3]:
        clean = re.sub(r'<[^>]+>', '', p).strip()
        print('  >', clean)

for no in [224473588453, 224473587062, 224473585203]:
    check_m_post(no)
