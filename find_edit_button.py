import time, re
from playwright.sync_api import sync_playwright

PROFILE_DIR = r"C:\Users\kwonf\.gemini\antigravity\scratch\chrome-naver-profile"
LOG_NO = "224481551902"

print(f"🚀 블로그 글 뷰 페이지 진입: {LOG_NO}", flush=True)

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        user_data_dir=PROFILE_DIR,
        channel="chrome",
        headless=True,
        args=["--disable-blink-features=AutomationControlled"]
    )
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.goto(f"https://blog.naver.com/kwonflower58/{LOG_NO}", wait_until="domcontentloaded")
    time.sleep(3)
    
    print("현재 URL:", page.url, flush=True)
    # Check iframe
    mf = None
    for f in page.frames:
        if "PostView" in f.url or "postview" in f.url or "kwonflower58" in f.url:
            mf = f
            break
    target_frame = mf if mf else page
    print(f"타겟 프레임 URL: {target_frame.url}", flush=True)
    
    # Find edit button
    edit_btns = target_frame.locator("a:has-text('수정'), button:has-text('수정'), .btn_edit, ._btn_edit, a[href*='postupdate'], a[href*='PostUpdateForm']")
    count = edit_btns.count()
    print(f"수정 버튼 수: {count}", flush=True)
    for i in range(count):
        print(f"  버튼 {i}: text='{edit_btns.nth(i).text_content()}', href='{edit_btns.nth(i).get_attribute('href')}'")
        
    page.screenshot(path="post_view_page.png")
    ctx.close()
