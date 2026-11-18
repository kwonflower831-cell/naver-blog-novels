import sys
import time
from playwright.sync_api import sync_playwright

PROFILE_DIR = r"C:\Users\kwonf\.gemini\antigravity\scratch\chrome-naver-profile"

print("🚀 [카테고리 즉시 변경] 네이버 블로그 관리자 글 관리 진입...", flush=True)

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        user_data_dir=PROFILE_DIR,
        channel="chrome",
        headless=False,
        args=["--start-maximized", "--disable-blink-features=AutomationControlled"],
        no_viewport=True,
    )
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.goto("https://admin.blog.naver.com/kwonflower58/post", wait_until="domcontentloaded", timeout=45000)
    time.sleep(4)
    
    print(f"현재 페이지 URL: {page.url}", flush=True)
    page.screenshot(path="admin_post_page.png")
    
    # Check if login required
    if "nid.naver.com" in page.url:
        print("로그인 페이지 감지됨", flush=True)
        ctx.close()
        sys.exit(1)
        
    # Find the post row for 13장
    print("글 목록에서 《유품》 13장 탐색 중...", flush=True)
    # Typically in a table. Let's find tr or label containing '유품' and '13'
    row = page.locator("tr:has-text('유품'):has-text('13')").first
    if row.count() > 0:
        print("✔ 13장 행 발견!", flush=True)
        chk = row.locator("input[type='checkbox']").first
        chk.click()
        time.sleep(1)
        
        # Click '카테고리 이동' button
        print("카테고리 이동 버튼 클릭...", flush=True)
        move_btn = page.locator("button:has-text('카테고리 이동'), a:has-text('카테고리 이동'), input[value*='카테고리 이동']").first
        move_btn.click()
        time.sleep(1.5)
        
        # In modal/dialog, select category '연재소설 유품'
        print("카테고리 선택 창에서 '유품' 선택...", flush=True)
        page.screenshot(path="move_modal.png")
        
        # Select target category in select or radio or tree
        cat_select = page.locator("select[name*='category'], select#changeCategorySelect, select#categoryNo")
        if cat_select.count() > 0:
            # find option with '유품'
            opts = cat_select.locator("option").evaluate_all("els => els.map(e => ({val: e.value, text: e.textContent}))")
            print("선택 가능한 카테고리 옵션:", opts, flush=True)
            for opt in opts:
                if "유품" in opt["text"]:
                    cat_select.select_option(value=opt["val"])
                    print(f"선택됨: {opt['text']} ({opt['val']})", flush=True)
                    break
        else:
            # Maybe list/radio
            target = page.locator("label:has-text('유품'), input[type='radio'][value='11']").first
            if target.count() > 0:
                target.click()
                print("라벨/라디오로 유품 선택 완료", flush=True)
                
        time.sleep(1)
        # Click modal confirm button
        confirm_btn = page.locator(".layer_popup button:has-text('확인'), .popup button:has-text('확인'), button:has-text('변경'), button:has-text('적용'), input[value='확인']").first
        if confirm_btn.count() > 0:
            confirm_btn.click()
            print("✔ 확인 버튼 클릭!", flush=True)
        time.sleep(3)
        page.screenshot(path="after_move.png")
        print("🎉 카테고리 이동 완료!", flush=True)
    else:
        print("❌ 목록에서 13장 글을 찾지 못함. 화면 HTML 분석 필요", flush=True)
        
    ctx.close()
