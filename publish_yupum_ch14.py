import ctypes
import os
import re
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

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
                    title = buff.value
                    if "네이버" in title or "로그인" in title or "Chrome" in title:
                        user32.ShowWindow(hwnd, 3) # SW_MAXIMIZE
                        user32.SetForegroundWindow(hwnd)
                        if hasattr(user32, "SwitchToThisWindow"):
                            user32.SwitchToThisWindow(hwnd, True)
            return True
        user32.EnumWindows(WNDENUMPROC(enum_cb), 0)
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent
novel_file = BASE_DIR / "novel-yupum-text" / "ch14-published.txt"

if not novel_file.exists():
    print(f"Error: {novel_file} not found!")
    sys.exit(1)

text = novel_file.read_text(encoding="utf-8").strip()
lines = text.splitlines()

# 제목 추출
title = "《유품》 14장. 밀폐된 방"
for line in lines[:5]:
    if line.strip().startswith("《유품》"):
        title = line.strip()
        break

# 본문 문단 추출
body_lines = []
skip_first = True
for line in lines:
    s = line.strip()
    if skip_first and (s.startswith("※") or s.startswith("《유품》") or not s):
        continue
    skip_first = False
    if s:
        body_lines.append(s)

tags = ["유품", "연재소설", "스릴러", "소설", "유품정리"]
category_name = "연재소설 유품"
PROFILE_DIR = r"C:\Users\kwonf\.gemini\antigravity\scratch\chrome-naver-profile"

print("=======================================================", flush=True)
print(f"🚀 네이버 블로그 자동 발행 시작: {title}", flush=True)
print(f"📄 문단 수: {len(body_lines)}개", flush=True)
print(f"🏷️ 태그: {tags}", flush=True)
print(f"📁 카테고리: {category_name}", flush=True)
print("=======================================================", flush=True)

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        user_data_dir=PROFILE_DIR,
        channel="chrome",
        headless=False,
        args=["--start-maximized", "--disable-blink-features=AutomationControlled"],
        no_viewport=True,
    )
    page = ctx.pages[0] if ctx.pages else ctx.new_page()

    # 1. 블로그 글쓰기 페이지 이동
    print("1. 글쓰기 페이지 접속 중...", flush=True)
    page.goto("https://blog.naver.com/kwonflower58?Redirect=Write&", wait_until="domcontentloaded")
    page.bring_to_front()
    bring_window_to_top()
    time.sleep(3)

    # 로그인 세션 확인
    if "nidlogin" in page.url or "nid.naver.com" in page.url:
        print("⚠️ 로그인 필요: 열린 Chrome 창에서 로그인을 완료해 주세요 (최대 300초 대기)...", flush=True)
        bring_window_to_top()
        page.screenshot(path=str(BASE_DIR / "login_needed.png"))
        for _ in range(300):
            if "nidlogin" not in page.url and "nid.naver.com" not in page.url:
                print("✓ 로그인 감지됨! 글쓰기 화면으로 이동합니다...", flush=True)
                time.sleep(3)
                break
            time.sleep(1)
        if "nidlogin" in page.url:
            print("로그인 시간 초과.", flush=True)
            ctx.close()
            sys.exit(1)

    # 2. 스마트에디터 프레임 탐색
    print("2. 에디터 프레임 탐색 중...", flush=True)
    frame = None
    for _ in range(30):
        for f in page.frames:
            try:
                if f.locator(".se-documentTitle").count() > 0 or f.locator(".se-component.se-text .se-text-paragraph").count() > 0:
                    frame = f
                    break
            except Exception:
                pass
        if frame:
            break
        time.sleep(1)

    if not frame:
        print("❌ 에디터 프레임을 찾을 수 없습니다!", flush=True)
        ctx.close()
        sys.exit(1)

    # 3. 팝업창 닫기 (작성 중인 글 취소 등)
    for sel in [".se-popup-button-cancel", ".se-help-panel-close-button"]:
        try:
            b = frame.locator(sel)
            if b.count() > 0 and b.first.is_visible():
                b.first.click()
                time.sleep(0.5)
        except Exception:
            pass

    # 4. 제목 입력
    print("3. 제목 입력 중...", flush=True)
    title_box = frame.locator(".se-documentTitle [contenteditable='true'], .se-documentTitle input").first
    title_box.click()
    time.sleep(0.3)
    page.keyboard.insert_text(title)
    time.sleep(0.5)

    # 5. 본문 입력
    print("4. 본문 단락 입력 중...", flush=True)
    body_box = frame.locator(".se-component.se-text .se-text-paragraph").first
    body_box.click()
    time.sleep(0.3)

    for i, para in enumerate(body_lines):
        page.keyboard.insert_text(para)
        time.sleep(0.01)
        if i < len(body_lines) - 1:
            page.keyboard.press("Enter")
            page.keyboard.press("Enter")
            time.sleep(0.01)

    time.sleep(1)

    # 6. 발행 패널 열기
    print("5. 발행 설정 패널 열기...", flush=True)
    frame.get_by_role("button", name="발행").first.click()
    time.sleep(2)

    # 7. 카테고리 선택
    print(f"6. 카테고리 '{category_name}' 선택 중...", flush=True)
    try:
        cat_btn = frame.get_by_role("button", name="카테고리 목록 버튼")
        if cat_btn.count() > 0:
            cat_btn.first.click()
            time.sleep(0.7)
            target_cat = frame.get_by_role("button", name=category_name)
            if target_cat.count() > 0:
                target_cat.first.click()
                time.sleep(0.5)
                print(f"   ✓ 카테고리 '{category_name}' 선택 완료", flush=True)
    except Exception as e:
        print("   카테고리 선택 알림:", e, flush=True)

    # 8. 태그 입력
    print("7. 태그 입력 중...", flush=True)
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
    except Exception as e:
        print("   태그 입력 알림:", e, flush=True)

    # 9. 최종 발행 버튼 클릭
    print("8. 최종 발행 실행...", flush=True)
    frame.get_by_role("button", name="발행").last.click()
    time.sleep(6)

    print("=======================================================", flush=True)
    print("🎉 네이버 블로그에 《유품》 14장 발행이 성공적으로 완료되었습니다!", flush=True)
    print("=======================================================", flush=True)
    ctx.close()
