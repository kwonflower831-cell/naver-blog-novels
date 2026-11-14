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
POST_PATH = BASE_DIR / "content-templates" / "tax-refund-and-hidden-money-kit" / "NAVER_BLOG_숨은환급금_연말정산_절세치트키_포스팅.md"
PROFILE_DIR = r"C:\Users\kwonf\.gemini\antigravity\scratch\chrome-naver-profile"

TITLE = "2026 숨은 돈 찾기 & 연말정산 환급금 꿀팁: 수수료 0원 정부 사이트 5선 (계산기 나눔)"

TAGS = [
    "연말정산환급금", "숨은돈찾기", "삼쩜삼수수료", "월세세액공제", "경정청구",
    "카드포인트현금화", "휴면예금찾기", "통신비미환급금", "2026연말정산", "절세계산기"
]

def load_post_paragraphs():
    raw = POST_PATH.read_text(encoding="utf-8").replace("\r\n", "\n")
    start_marker = "[블로그 본문 시작"
    end_marker = "### [네이버 블로그 태그 추천"

    start_idx = raw.find(start_marker)
    if start_idx != -1:
        start_idx = raw.find("\n", start_idx) + 1
        while raw[start_idx:start_idx+10].startswith("---") or raw[start_idx:start_idx+10].startswith("###") or raw[start_idx:start_idx+2] == "\n":
            start_idx = raw.find("\n", start_idx) + 1
    else:
        start_idx = 0

    end_idx = raw.find(end_marker)
    if end_idx == -1:
        end_idx = len(raw)

    body = raw[start_idx:end_idx].strip()
    paras = [p.strip() for p in body.split("\n\n") if p.strip() and not p.strip().startswith("---")]
    return paras

def bring_window_to_top():
    try:
        user32 = ctypes.windll.user32
        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
        def enum_cb(hwnd, lparam):
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buff = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buff, length + 1)
                title = buff.value
                if "네이버" in title or "로그인" in title or "Chrome" in title:
                    user32.ShowWindow(hwnd, 3) # SW_MAXIMIZE
                    user32.SetForegroundWindow(hwnd)
            return True
        user32.EnumWindows(WNDENUMPROC(enum_cb), 0)
    except Exception as e:
        pass

def find_editor_frame(page, timeout_sec=35):
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

def is_login_required(page):
    u = page.url.lower()
    return "nidlogin" in u or "nid.naver.com" in u

def is_blog_editor_ready(page):
    u = page.url.lower()
    return ("blog.naver.com" in u or "postwrite" in u) and "nidlogin" not in u and "nid.naver.com" not in u

def publish():
    paras = load_post_paragraphs()
    print(f"로드된 본문 단락 수: {len(paras)}개", flush=True)

    with sync_playwright() as p:
        print("크롬 브라우저를 시작합니다...", flush=True)
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_DIR,
            channel="chrome",
            headless=False,
            args=["--start-maximized", "--disable-blink-features=AutomationControlled"],
            no_viewport=True,
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()

        print("네이버 블로그 글쓰기 페이지 접속 중...", flush=True)
        try:
            page.goto("https://blog.naver.com/kwonflower58?Redirect=Write&", wait_until="domcontentloaded", timeout=60000)
        except Exception as e:
            print("페이지 접속 안내:", e, flush=True)
        time.sleep(3.5)

        if is_login_required(page):
            print("로그인이 필요합니다. 로그인 창으로 이동합니다...", flush=True)
            page.goto("https://nid.naver.com/nidlogin.login?url=https%3A%2F%2Fblog.naver.com%2Fkwonflower58%3FRedirect%3DWrite%26", wait_until="domcontentloaded", timeout=60000)
            page.bring_to_front()
            bring_window_to_top()

            def show_popup():
                try:
                    ctypes.windll.user32.MessageBoxW(
                        0,
                        "화면에 열린 크롬 창에서 네이버 로그인을 완료해 주세요.\n\n"
                        "※ 아이디/비밀번호 또는 네이버 앱의 QR코드 로그인 모두 가능합니다.\n"
                        "로그인이 확인되면 제목, 본문, 태그 입력 및 전체공개 발행이 전자동으로 진행됩니다.",
                        "블로그 전자동 발행 안내",
                        0x40 | 0x10000
                    )
                except Exception:
                    pass
            threading.Thread(target=show_popup, daemon=True).start()

            logged_in = False
            for sec in range(900):
                cookies = ctx.cookies()
                has_auth = any(c.get("name") in ("NID_AUT", "NID_SES") for c in cookies)
                ready = is_blog_editor_ready(page)
                if has_auth or ready:
                    print(f"로그인 감지 성공! (has_auth={has_auth}, ready={ready})", flush=True)
                    logged_in = True
                    time.sleep(2.0)
                    break
                if sec % 30 == 0 and sec > 0:
                    print(f"로그인 대기 중 ({sec}초 경과)...", flush=True)
                time.sleep(1)

            if not logged_in:
                raise RuntimeError("네이버 로그인 대기 시간 초과")

        if "Redirect=Write" not in page.url and "PostWriteForm" not in page.url:
            print("에디터 페이지로 이동 중...", flush=True)
            page.goto("https://blog.naver.com/kwonflower58?Redirect=Write&", wait_until="domcontentloaded", timeout=60000)
        time.sleep(5.0)

        print("에디터 프레임 탐색 중...", flush=True)
        mf = find_editor_frame(page, timeout_sec=35)
        dismiss_editor_popups(mf)

        # 1. 제목 입력
        print(f"제목 입력: {TITLE}", flush=True)
        title_box = mf.locator(".se-documentTitle .se-ff-nanumgothic, .se-documentTitle input, .se-documentTitle [contenteditable='true']").first
        title_box.click()
        time.sleep(0.5)
        page.keyboard.insert_text(TITLE)
        time.sleep(0.5)

        # 2. 본문 입력
        print("본문 문단 자동 타이핑 입력 중...", flush=True)
        bl = mf.locator(".se-component.se-text .se-text-paragraph").first
        bl.click()
        time.sleep(0.4)

        for i, para in enumerate(paras):
            page.keyboard.insert_text(para)
            time.sleep(0.06)
            if i < len(paras) - 1:
                page.keyboard.press("Enter")
                time.sleep(0.06)
                page.keyboard.press("Enter")
                time.sleep(0.06)

        time.sleep(1.0)
        print("본문 입력 완료!", flush=True)

        # 3. 우측 상단 발행 버튼 클릭
        print("발행 패널 여는 중...", flush=True)
        mf.get_by_role("button", name="발행").first.click()
        time.sleep(2.0)

        # 4. 태그 입력
        print("태그 자동 입력 중...", flush=True)
        tag_box = mf.get_by_role("combobox", name=re.compile(r"^태그"))
        if tag_box.count() > 0:
            tag_box.first.click()
        else:
            mf.locator('input[placeholder*="태그"], [aria-label*="태그"], [id*="tag-input"]').first.click()

        for tg in TAGS[:10]:
            page.keyboard.insert_text(tg)
            page.keyboard.press("Enter")
            time.sleep(0.2)
        print("태그 입력 완료!", flush=True)

        # 5. 전체공개 확인
        print("전체공개 확인...", flush=True)
        try:
            mf.locator('label[for="open_all"], input#open_all, label:has-text("전체공개")').first.click()
            time.sleep(0.5)
        except Exception:
            pass

        # 6. 최종 발행 버튼 클릭
        print("최종 [발행] 버튼 클릭 중...", flush=True)
        mf.get_by_role("button", name="발행").last.click()
        time.sleep(6.0)

        print("🎉 축하합니다! 포스팅이 성공적으로 전체공개 발행되었습니다!", flush=True)
        time.sleep(3)
        page.close()
        ctx.close()

if __name__ == "__main__":
    publish()
