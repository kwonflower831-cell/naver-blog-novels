import ctypes
import os
import re
import sys
import threading
import time
import argparse
from pathlib import Path
from playwright.sync_api import sync_playwright

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

BASE_DIR = Path(r"C:\Users\kwonf\.gemini\antigravity\scratch\novels")
TEXT_DIR = BASE_DIR / "novel-evidence4-text"
PROFILE_DIR = r"C:\Users\kwonf\.gemini\antigravity\scratch\chrome-naver-profile"

DEFAULT_TAGS = ["증거물4호", "연재소설", "스릴러소설", "추리소설", "웹소설", "미스터리", "완결소설"]

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
        pass

def is_logged_in(ctx, page):
    cookies = ctx.cookies()
    has_auth = any(c.get("name") in ("NID_AUT", "NID_SES") for c in cookies)
    if has_auth:
        return True
    u = page.url.lower()
    return "nidlogin" not in u and "nid.naver.com" not in u and ("blog.naver.com" in u or "postwrite" in u)

def ensure_session(ctx, page):
    """네이버 로그인 세션 확인 및 필요 시 QR 로그인 화면 안내"""
    print("🔒 [1단계] 네이버 로그인 세션 확인 중...", flush=True)
    try:
        page.goto("https://blog.naver.com/kwonflower58?Redirect=Write&", wait_until="domcontentloaded", timeout=30000)
    except Exception:
        pass
    time.sleep(2.5)

    if not is_logged_in(ctx, page):
        print("⚠️ 세션 필요: 네이버 로그인 화면으로 이동합니다 (QR코드 우선)...", flush=True)
        page.goto("https://nid.naver.com/nidlogin.login?mode=qrcode&url=https%3A%2F%2Fblog.naver.com%2Fkwonflower58%3FRedirect%3DWrite%26", wait_until="domcontentloaded")
        page.bring_to_front()
        bring_window_to_top()

        def show_popup():
            try:
                ctypes.windll.user32.MessageBoxW(
                    0,
                    "화면에 열린 크롬 창에서 네이버 로그인을 1회 완료해 주세요.\n\n"
                    "※ 네이버 앱 QR코드를 찍으시거나 아이디/비밀번호로 로그인하시면 됩니다.\n"
                    "로그인하시면 즉시 《증거물 4호》 6장~12장 일괄 자동 발행이 시작됩니다!",
                    "네이버 1회 로그인 안내",
                    0x40 | 0x10000
                )
            except Exception:
                pass
        threading.Thread(target=show_popup, daemon=True).start()

        print("👉 스마트폰 네이버 앱의 [QR코드]를 찍으시거나 로그인을 완료해 주세요...", flush=True)
        logged_in = False
        for sec in range(900):
            if is_logged_in(ctx, page):
                print(f"🎉 로그인 감지 성공! (경과: {sec}초)", flush=True)
                logged_in = True
                time.sleep(3.0)
                break
            if sec > 0 and sec % 15 == 0:
                print(f"로그인 대기 중 ({sec}초 경과)...", flush=True)
            time.sleep(1)

        if not logged_in:
            raise RuntimeError("로그인 대기 시간 초과")

    print("✅ [세션 정상] 로그인 세션이 확인되었습니다!", flush=True)

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

def parse_chapter_file(ch_num):
    pub_path = TEXT_DIR / f"ch{ch_num}-published.txt"
    if not pub_path.exists():
        raise FileNotFoundError(f"게시본 파일이 없습니다: {pub_path}")
    raw = pub_path.read_text(encoding="utf-8").replace("\r\n", "\n").strip()
    paras = [p.strip() for p in raw.split("\n\n") if p.strip()]
    
    # 3번째 줄(또는 2번째 비어있지 않은 단락)에서 제목 추출
    title = f"《증거물 4호》 {ch_num}장"
    lines = raw.split("\n")
    for line in lines[:5]:
        if "《증거물 4호》" in line:
            title = line.strip()
            break
            
    return title, paras

def publish_single_chapter(page, ch_num):
    title, paragraphs = parse_chapter_file(ch_num)
    
    print("\n" + "=" * 65, flush=True)
    print(f"🚀 [《증거물 4호》 {ch_num}장 블로그 자동 발행 시작]", flush=True)
    print(f"📌 제목: {title}", flush=True)
    print(f"📄 문단 수: {len(paragraphs)}개", flush=True)
    print("=" * 65, flush=True)

    print("1. 에디터 진입 중...", flush=True)
    page.goto("https://blog.naver.com/kwonflower58?Redirect=Write&", wait_until="domcontentloaded", timeout=60000)
    time.sleep(4.0)

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
        time.sleep(0.03)
        if i < len(paragraphs) - 1:
            page.keyboard.press("Enter")
            time.sleep(0.03)
            page.keyboard.press("Enter")
            time.sleep(0.03)

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
            tag_box.click()
        else:
            mf.locator('input[placeholder*="태그"], [aria-label*="태그"], [id*="tag-input"]').first.click()
        for tg in DEFAULT_TAGS:
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
    print(f"🎉 [발행 성공!] 《증거물 4호》 {ch_num}장이 성공적으로 발행되었습니다!", flush=True)
    print("=" * 65 + "\n", flush=True)
    return True

def main():
    parser = argparse.ArgumentParser(description="《증거물 4호》 네이버 블로그 일괄 순차 발행")
    parser.add_argument("--start", type=int, default=6, help="시작 장 번호 (기본: 6)")
    parser.add_argument("--end", type=int, default=12, help="종료 장 번호 (기본: 12)")
    parser.add_argument("--cooldown", type=int, default=20, help="장 간 안전 대기 시간(초) (기본: 20)")
    args = parser.parse_args()

    chapters = list(range(args.start, args.end + 1))
    print("=" * 65, flush=True)
    print(f"📚 [《증거물 4호》 일괄 순차 발행 작업 준비]")
    print(f"📌 대상 회차: {chapters} (총 {len(chapters)}개 회차)")
    print(f"⏱️ 회차 간 안전 쿨타임: {args.cooldown}초")
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

        # 1회 세션 확인 및 필요 시 로그인 안내
        ensure_session(ctx, page)

        for idx, ch in enumerate(chapters):
            print(f"\n>>> [{idx + 1}/{len(chapters)}] {ch}장 발행 진행 중...", flush=True)
            success = publish_single_chapter(page, ch)
            if not success:
                print(f"❌ {ch}장 발행 중 문제가 발생하여 중단합니다.", flush=True)
                break

            if idx < len(chapters) - 1:
                print(f"⏳ 다음 장({chapters[idx + 1]}장) 발행 전 안전 대기 {args.cooldown}초...", flush=True)
                time.sleep(args.cooldown)

        print("\n" + "★" * 65, flush=True)
        print("🎊 [모든 회차 발행 완료!] 《증거물 4호》 일괄 발행이 끝났습니다!")
        print("★" * 65 + "\n", flush=True)

        time.sleep(3)
        page.close()
        ctx.close()

if __name__ == "__main__":
    main()
