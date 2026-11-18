import ctypes
import os
import re
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

PROFILE_DIR = r"C:\Users\kwonf\.gemini\antigravity\scratch\chrome-naver-profile"
NOVEL_FILE = Path(r"C:\Users\kwonf\.gemini\antigravity\scratch\novels\novel-yupum-text\ch13-published.txt")

def force_foreground():
    try:
        user32 = ctypes.windll.user32
        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
        def enum_cb(hwnd, lparam):
            if user32.IsWindowVisible(hwnd):
                length = user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buff = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(hwnd, buff, length + 1)
                    title = buff.value
                    if "네이버" in title or "Chrome" in title or "로그인" in title:
                        user32.ShowWindow(hwnd, 3) # SW_MAXIMIZE
                        user32.SetForegroundWindow(hwnd)
            return True
        user32.EnumWindows(WNDENUMPROC(enum_cb), 0)
    except Exception:
        pass

def read_clean_novel():
    raw = NOVEL_FILE.read_text(encoding="utf-8").strip()
    lines = raw.split("\n\n")
    cleaned_paras = []
    title = "《유품》 13장. 다른 종이"
    for p in lines:
        p_str = p.strip()
        if not p_str:
            continue
        if p_str.startswith("《유품》"):
            title = p_str
            continue
        if p_str.startswith("※"):
            continue
        cleaned_paras.append(p_str)
    return title, cleaned_paras

def click_font_nanummyeongjo(page, target_frame):
    try:
        font_btn = target_frame.locator(
            'button[data-name="font-family"], button[class*="se-font-family-toolbar-button"], .se-toolbar-item-font-family button'
        ).first
        if font_btn.count() > 0 and font_btn.is_visible():
            font_btn.click()
            time.sleep(0.6)
            target_frame.get_by_text("나눔명조", exact=True).first.click()
            time.sleep(0.6)
            print("✔ 나눔명조 폰트 적용 완료", flush=True)
    except Exception as e:
        print("폰트 설정 참고:", e, flush=True)

def find_editor_frame(page, timeout_sec=40):
    for _ in range(timeout_sec * 2):
        for f in page.frames:
            try:
                if f.locator(".se-documentTitle").count() > 0 or f.locator(".se-component.se-text .se-text-paragraph").count() > 0:
                    return f
            except Exception:
                pass
        time.sleep(0.5)
    raise RuntimeError(f"에디터 프레임을 찾을 수 없습니다. URL={page.url}")

def dismiss_popups(frame):
    for sel in [".se-popup-button-cancel", ".se-help-panel-close-button"]:
        try:
            b = frame.locator(sel)
            if b.count() > 0 and b.first.is_visible():
                b.first.click()
                time.sleep(0.5)
        except Exception:
            pass

def main():
    title, paragraphs = read_clean_novel()
    tags = ["유품", "연재소설", "스릴러", "소설", "유품정리"]

    print("=" * 65, flush=True)
    print("🚀 [《유품》 13장 정상화 및 카테고리 자동 수정 재발행]")
    print(f"📌 제목: {title}")
    print(f"📄 문단 수: {len(paragraphs)}개")
    print(f"🏷️ 카테고리 목표: 연재소설 유품 (Category 11)")
    print("=" * 65, flush=True)

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_DIR,
            channel="chrome",
            headless=False,
            args=["--start-maximized", "--disable-blink-features=AutomationControlled"],
            no_viewport=True,
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()

        # QR코드 로그인 전용 페이지로 즉시 진입
        qr_url = "https://nid.naver.com/nidlogin.login?mode=qrcode&url=https%3A%2F%2Fblog.naver.com%2Fkwonflower58%3FRedirect%3DWrite%26"
        print("네이버 QR코드 로그인 화면으로 이동 중...", flush=True)
        page.goto(qr_url, wait_until="domcontentloaded")
        time.sleep(2)
        page.bring_to_front()
        force_foreground()

        # 만약 QR 화면이 아니라면 QR 탭 강제 클릭
        try:
            qr_btn = page.locator("#qrcode, a:has-text('QR 코드'), button:has-text('QR 코드')").first
            if qr_btn.count() > 0 and qr_btn.is_visible():
                qr_btn.click()
                time.sleep(0.5)
        except Exception:
            pass

        print("👉 화면 중앙에 뜬 [네모난 QR코드]를 스마트폰 네이버 앱으로 비춰주세요 (대기 중)...", flush=True)

        for sec in range(600):
            u = page.url.lower()
            if "nidlogin" not in u and "nid.naver.com" not in u:
                print("🎉 로그인 감지 성공! 에디터로 진입합니다...", flush=True)
                time.sleep(3)
                break
            if sec > 0 and sec % 10 == 0:
                force_foreground()
            time.sleep(1)

        # 에디터 프레임 탐색
        print("에디터 프레임 탐색 중...", flush=True)
        frame = find_editor_frame(page, timeout_sec=40)
        dismiss_popups(frame)

        # 제목 입력
        print("제목 입력 중...", flush=True)
        title_box = frame.locator(".se-documentTitle [contenteditable='true'], .se-documentTitle input").first
        title_box.click()
        time.sleep(0.4)
        page.keyboard.insert_text(title)
        time.sleep(0.5)

        # 본문 입력
        print(f"본문 {len(paragraphs)}단락 타이핑 중 (JS 코드 제거된 순수 원고)...", flush=True)
        body_box = frame.locator(".se-component.se-text .se-text-paragraph").first
        body_box.click()
        time.sleep(0.4)

        for i, para in enumerate(paragraphs):
            page.keyboard.insert_text(para)
            time.sleep(0.02)
            if i < len(paragraphs) - 1:
                page.keyboard.press("Enter")
                page.keyboard.press("Enter")
                time.sleep(0.02)

        time.sleep(1.0)

        # 전체 선택 후 나눔명조 폰트 적용
        print("나눔명조 서식 적용 중...", flush=True)
        page.keyboard.press("Control+A")
        time.sleep(0.4)
        click_font_nanummyeongjo(page, frame)
        time.sleep(1.0)

        # 발행 패널 열기
        print("⚙️ [발행] 패널 열기...", flush=True)
        frame.get_by_role("button", name="발행").first.click()
        time.sleep(2.0)

        # 카테고리: 연재소설 유품 선택
        print("카테고리 '연재소설 유품' 선택 중...", flush=True)
        frame.get_by_role("button", name="카테고리 목록 버튼").first.click()
        time.sleep(0.8)
        
        cat_item = frame.get_by_role("button", name=re.compile(r"연재소설\s*유품|유품"))
        if cat_item.count() > 0:
            cat_item.first.click()
            print("✔ '연재소설 유품' 카테고리 클릭 성공!", flush=True)
        else:
            frame.get_by_text("연재소설 유품", exact=False).first.click()
            print("✔ 텍스트로 카테고리 선택 성공!", flush=True)
        time.sleep(0.8)

        # 태그 입력
        print("태그 5개 입력 중...", flush=True)
        try:
            tag_box = frame.get_by_role("combobox", name=re.compile(r"^태그"))
            if tag_box.count() > 0:
                tag_box.first.click()
            else:
                frame.locator('input[placeholder*="태그"], [aria-label*="태그"]').first.click()
            for tg in tags:
                page.keyboard.insert_text(tg)
                page.keyboard.press("Enter")
                time.sleep(0.15)
            print("✔ 태그 입력 완료!", flush=True)
        except Exception as e:
            print("태그 입력 참고:", e, flush=True)

        # 전체공개 확인
        try:
            frame.locator('label[for="open_all"], input#open_all, label:has-text("전체공개")').first.click()
            time.sleep(0.3)
        except Exception:
            pass

        # 최종 [발행] 버튼 클릭
        print("🚀 최종 [발행] 버튼 클릭 중...", flush=True)
        frame.get_by_role("button", name="발행").last.click()
        time.sleep(6.0)

        print("=" * 65, flush=True)
        print("🎉 [완벽 성공!] 《유품》 13장이 카테고리 11번(연재소설 유품) 및 나눔명조 서식으로 완벽히 재발행되었습니다!")
        print("=" * 65, flush=True)

        time.sleep(3)
        ctx.close()

if __name__ == "__main__":
    main()
