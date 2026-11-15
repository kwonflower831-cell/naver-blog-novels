import urllib.request
import re
import urllib.parse

url = 'https://blog.naver.com/PostTitleListAsync.naver?blogId=kwonflower58&currentPage=1&countPerPage=30'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as resp:
    html = resp.read().decode('utf-8')

for m in re.findall(r'"logNo":"(\d+)","title":"([^"]+)","categoryNo":"(\d+)"', html):
    title = urllib.parse.unquote(m[1].replace("+", " "))
    print(f"{m[0]}: {title} (cat: {m[2]})")
