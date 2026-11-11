import urllib.request, re, urllib.parse

req = urllib.request.Request(
    'https://blog.naver.com/PostTitleListAsync.naver?blogId=kwonflower58&currentPage=1&categoryNo=11&countPerPage=15',
    headers={'User-Agent': 'Mozilla/5.0'}
)
with urllib.request.urlopen(req, timeout=15) as resp:
    txt = resp.read().decode('utf-8', errors='replace')

matches = re.findall(r'"logNo":"(\d+)","title":"([^"]*)"', txt)
for log_no, title in matches:
    clean_title = urllib.parse.unquote(title.replace('+', ' '))
    print(f"{log_no}: {clean_title}")
