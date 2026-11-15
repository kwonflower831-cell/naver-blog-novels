import ctypes
import os
import re
import sys
import threading
import time
import urllib.parse
import urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

BASE_DIR = Path(r"C:\Users\kwonf\.gemini\antigravity\scratch\novels")
CH6_PATH = BASE_DIR / "novel-evidence4-text" / "ch6-published.txt"
PROFILE_DIR = r"C:\Users\kwonf\.gemini\antigravity\scratch\chrome-naver-profile"

raw6 = CH6_PATH.read_text(encoding="utf-8").replace("\r\n", "\n").strip()
paragraphs = [p.strip() for p in raw6.split("\n\n") if p.strip()]

title = "《증거물 4호》 6장. 정전"
tags = ["증거물4호", "연재소설", "스릴러소설", "추리소설", "웹소설"]

print(f"Loaded Ch6 paragraphs: {len(paragraphs)}", flush=True)

def bring_window_to_top():
    try:
        user32 = ctypes.windll.user32
        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
        def enum_cb(hwnd, lparam):
            if user32.IsWindowVisible(hwnd):
                length = user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buff = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(hwnd, buff, length + 1)
                    t = buff.value
                    if "네이버" in t or "로그인" in t or "Chrome" in t:
                        user32.ShowWindow(hwnd, 3)
                        user32.SetForegroundWindow(hwnd)
            return True
        user32.EnumWindows(WNDENUMPROC(enum_cb), 0)
    except Exception as e:
        print("bring_window_to_top note:", e, flush=True)

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

def dismiss_editor_popups(frame):
    for sel in [".se-popup-button-cancel", ".se-help-panel-close-button"]:
        try:
            btn = frame.locator(sel)
            if btn.count() > 0 and btn.first.is_visible():
                btn.first.click()
                time.sleep(0.5)
        except Exception:
            pass

def click_font_nanummyeongjo(page, target_frame):
    try:
        font_btn = target_frame.locator(
            'button[data-name="font-family"], button[class*="se-font-family-toolbar-button"], .se-toolbar-item-font-family button'
        ).first
        if font_btn.count() > 0 and font_btn.is_visible():
            font_btn.click()
        else:
            page.mouse.click(112, 121)
    except Exception:
        page.mouse.click(112, 121)
        
    time.sleep(0.8)
    try:
        target_frame.get_by_text("나눔명조", exact=True).first.click()
    except Exception:
        pass
    time.sleep(0.8)

def publish_ch6():
    print("=" * 65, flush=True)
    print("🚀 [《증거물 4호》 6장 블로그 자동 발행 시작]", flush=True)
    print(f"📌 제목: {title}", flush=True)
    print(f"📄 문단 수: {len(paragraphs)}개", flush=True)
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

        print("1. 에디터 진입 중...", flush=True)
        page.goto("https://blog.naver.com/kwonflower58?Redirect=Write&", wait_until="domcontentloaded", timeout=60000)
        time.sleep(5.0)

        # 로그인 풀림 체크
        if "nidlogin" in page.url or "nid.naver.com" in page.url:
            print("⚠️ 네이버 로그인이 필요합니다. QR 코드로 1회 로그인해 주세요...", flush=True)
            bring_window_to_top()
            for _ in range(300):
                time.sleep(2)
                if "nidlogin" not in page.url and "nid.naver.com" not in page.url:
                    print("🎉 로그인 감지 성공!", flush=True)
                    break

        print("2. 에디터 프레임 탐색 및 팝업 닫기...", flush=True)
        mf = find_editor_frame(page, timeout_sec=40)
        dismiss_editor_popups(mf)

        # 제목 입력
        print(f"3. 제목 입력 중: {title}", flush=True)
        title_box = mf.locator(".se-documentTitle .se-ff-nanumgothic, .se-documentTitle input, .se-documentTitle [contenteditable='true']").first
        title_box.click()
        time.sleep(0.5)
        page.keyboard.insert_text(title)
        time.sleep(0.5)

        # 본문 입력
        print("4. 본문 단락 타이핑 입력 중...", flush=True)
        body_start = mf.locator(".se-component.se-text .se-text-paragraph").first
        body_start.click()
        time.sleep(0.4)

        for i, para in enumerate(paragraphs):
            page.keyboard.insert_text(para)
            time.sleep(0.04)
            if i < len(paragraphs) - 1:
                page.keyboard.press("Enter")
                time.sleep(0.04)
                page.keyboard.press("Enter")
                time.sleep(0.04)

        time.sleep(1.0)
        print("✔ 본문 입력 완료!", flush=True)

        # 글꼴 나눔명조 적용
        print("5. 글꼴 나눔명조 적용 중...", flush=True)
        try:
            mf.locator(".se-component.se-text .se-text-paragraph").nth(2).click()
            page.keyboard.press("Control+A")
            time.sleep(0.3)
            click_font_nanummyeongjo(page, mf)
        except Exception as e:
            print(f"나눔명조 적용 시도 중 알림: {e}", flush=True)

        # 발행 패널 열기
        print("6. 발행 패널 열기...", flush=True)
        mf.get_by_role("button", name="발행").first.click()
        time.sleep(2.0)

        # 카테고리 선택
        print("7. 카테고리 '연재소설 증거물 4호' 선택...", flush=True)
        try:
            cat_list_btn = mf.get_by_role("button", name="카테고리 목록 버튼")
            if cat_list_btn.count() > 0:
                cat_list_btn.first.click()
                time.sleep(0.8)
            cat_target = mf.get_by_role("button", name=re.compile(r"증거물\s*4호"))
            if cat_target.count() > 0:
                cat_target.first.click()
                time.sleep(0.6)
                print("✔ '연재소설 증거물 4호' 카테고리 선택 완료!", flush=True)
        except Exception as e:
            print(f"카테고리 선택 중 알림: {e}", flush=True)

        # 태그 입력
        print("8. 태그 입력 중...", flush=True)
        try:
            tag_box = mf.get_by_role("combobox", name=re.compile(r"^태그"))
            if tag_box.count() > 0:
                tag_box.first.click()
            else:
                mf.locator('input[placeholder*="태그"], [aria-label*="태그"], [id*="tag-input"]').first.click()
            for tg in tags:
                page.keyboard.insert_text(tg)
                page.keyboard.press("Enter")
                time.sleep(0.2)
            print("✔ 태그 입력 완료!", flush=True)
        except Exception as e:
            print(f"태그 입력 중 알림: {e}", flush=True)

        # 전체공개 확인
        try:
            mf.locator('label[for="open_all"], input#open_all, label:has-text("전체공개")').first.click()
            time.sleep(0.4)
        except Exception:
            pass

        # 최종 발행 클릭
        print("9. 최종 [발행] 버튼 클릭...", flush=True)
        mf.get_by_role("button", name="발행").last.click()
        time.sleep(6.0)

        print("\n" + "=" * 65, flush=True)
        print("🎉 [성공!] 《증거물 4호》 6장이 성공적으로 발행되었습니다!", flush=True)
        print("=" * 65 + "\n", flush=True)

        time.sleep(3)
        page.close()
        ctx.close()
        return True

if __name__ == "__main__":
    publish_ch6()
