import urllib.request, re, urllib.parse

all_posts = []
for page in range(1, 10):
    url = f"https://blog.naver.com/PostTitleListAsync.naver?blogId=kwonflower58&currentPage={page}&countPerPage=30"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            txt = resp.read().decode('utf-8', errors='replace')
        matches = re.findall(r'"logNo":"(\d+)","title":"([^"]*)","categoryNo":"(\d+)"', txt)
        if not matches:
            break
        for m in matches:
            clean_title = urllib.parse.unquote(m[1].replace('+', ' '))
            all_posts.append((m[0], clean_title, m[2]))
        if len(matches) < 30:
            break
    except Exception as e:
        print(f"Page {page} error:", e)
        break

print(f"Total posts across all pages: {len(all_posts)}")
affiliate_keywords = ['비교', '가격', '원', 'vs', '할인', '구매', '쇼핑', '배송', '시리얼', '떡국', '린스', '식용유']
affiliate_posts = []
for log_no, title, cat in all_posts:
    is_cat6 = (cat == '6')
    has_kw = any(k in title for k in affiliate_keywords) and not ('유품' in title or '통화' in title or '체크아웃' in title or '장.' in title or '화.' in title)
    if is_cat6 or has_kw:
        affiliate_posts.append((log_no, title, cat))
        print(f"🎯 제휴/상품 글 발견: [{cat}] {log_no} - {title}")

print(f"\n총 발견된 제휴상품 관련 글: {len(affiliate_posts)}개")
