import urllib.request, re

def check_post(no):
    url = f'https://blog.naver.com/PostView.naver?blogId=kwonflower58&logNo={no}&redirect=Dlog'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    txt = urllib.request.urlopen(req).read().decode('utf-8', errors='replace')
    title = re.findall(r'<title>([\s\S]*?)</title>', txt)
    paras = re.findall(r'<p class="se-text-paragraph[^"]*">([\s\S]*?)</p>', txt)
    print(f'Post {no}: title={title[0] if title else ""}, paras={len(paras)}')

for no in [224473588453, 224473587062, 224473585203]:
    check_post(no)
