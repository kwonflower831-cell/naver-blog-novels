import urllib.request, re, urllib.parse

req = urllib.request.Request(
    'https://blog.naver.com/PostTitleListAsync.naver?blogId=kwonflower58&currentPage=1&countPerPage=20',
    headers={'User-Agent': 'Mozilla/5.0'}
)
with urllib.request.urlopen(req, timeout=15) as resp:
    txt = resp.read().decode('utf-8', errors='replace')

matches = re.findall(r'"logNo":"(\d+)","title":"([^"]*)","categoryNo":"(\d+)"', txt)
print(f"Total found: {len(matches)}")
for log_no, title, cat in matches:
    clean_title = urllib.parse.unquote(title.replace('+', ' '))
    print(f"{log_no} (cat {cat}): {clean_title}")
