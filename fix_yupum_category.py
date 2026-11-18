import re
import time
from playwright.sync_api import sync_playwright

PROFILE_DIR = r"C:\Users\kwonf\.gemini\antigravity\scratch\chrome-naver-profile"
LOG_NO = "224481551902"

print(f"🔧 [카테고리 수정] 《유품》 13장 (logNo: {LOG_NO}) 카테고리 11번으로 변경 시작...", flush=True)

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        user_data_dir=PROFILE_DIR,
        channel="chrome",
        headless=True,
        args=["--disable-blink-features=AutomationControlled"]
    )
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.goto(f"https://blog.naver.com/kwonflower58/postupdate?logNo={LOG_NO}", wait_until="domcontentloaded", timeout=45000)
    time.sleep(5)
    
    # Check frame
    frame = None
    for _ in range(30):
        for f in page.frames:
            try:
                if f.locator(".se-documentTitle").count() > 0 or f.locator(".se-component.se-text").count() > 0:
                    frame = f
                    break
            except Exception:
                pass
        if frame:
            break
        time.sleep(1)
        
    if not frame:
        print("❌ 에디터 프레임을 찾을 수 없습니다.", flush=True)
        ctx.close()
        exit(1)
        
    # Dismiss popups
    for sel in [".se-popup-button-cancel", ".se-help-panel-close-button"]:
        try:
            b = frame.locator(sel)
            if b.count() > 0 and b.first.is_visible():
                b.first.click()
                time.sleep(0.5)
        except Exception:
            pass
            
    # Open publish modal
    print("발행 패널 여는 중...", flush=True)
    frame.get_by_role("button", name="발행").first.click()
    time.sleep(2)
    
    # Select category
    print("카테고리 목록 버튼 클릭...", flush=True)
    frame.get_by_role("button", name="카테고리 목록 버튼").first.click()
    time.sleep(1)
    
    # Click '연재소설 유품' or '유품'
    cat_btn = frame.get_by_role("button", name=re.compile(r"유품"))
    if cat_btn.count() > 0:
        cat_btn.first.click()
        print("✔ '연재소설 유품' 카테고리 선택 완료!", flush=True)
    else:
        # try clicking by text
        frame.get_by_text("유품", exact=False).first.click()
        print("✔ 텍스트로 '유품' 카테고리 선택 완료!", flush=True)
    time.sleep(1)
    
    # Final publish button
    print("수정 [발행] 버튼 클릭...", flush=True)
    frame.get_by_role("button", name="발행").last.click()
    time.sleep(5)
    print("🎉 카테고리 변경 및 재발행 완료!", flush=True)
    ctx.close()
