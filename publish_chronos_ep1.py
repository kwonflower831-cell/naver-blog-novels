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
CH1_PATH = Path(r"D:\사용자\storyops\novels\chronos_arcana\chapters\ch1-draft.txt")

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
                        if hasattr(user32, "SwitchToThisWindow"):
                            user32.SwitchToThisWindow(hwnd, True)
            return True
        user32.EnumWindows(WNDENUMPROC(enum_cb), 0)
    except Exception:
        pass

def is_logged_in(ctx, page):
    cookies = ctx.cookies()
    has_auth = any(c.get("name") in ("NID_AUT", "NID_SES") for c in cookies)
    if has_auth:
        return True
    u = page.url.lower()
    return "nidlogin" not in u and "nid.naver.com" not in u and ("blog.naver.com" in u or "postwrite" in u)

def ensure_session(ctx, page):
    print("🔒 [1단계] 네이버 로그인 세션 확인 중...", flush=True)
    try:
        page.goto("https://blog.naver.com/kwonflower58?Redirect=Write&", wait_until="domcontentloaded", timeout=25000)
    except Exception:
        pass
    time.sleep(2.5)

    if not is_logged_in(ctx, page):
        print("⚠️ 네이버 로그인 화면으로 이동합니다 (화면 맨 앞으로 띄움)...", flush=True)
        page.goto("https://nid.naver.com/nidlogin.login?mode=qrcode&url=https%3A%2F%2Fblog.naver.com%2Fkwonflower58%3FRedirect%3DWrite%26", wait_until="domcontentloaded")
        page.bring_to_front()
        time.sleep(1)
        force_foreground()

        print("👉 화면에 표시된 크롬 창에서 [QR코드]를 스마트폰 네이버 앱으로 찍어주세요 (대기 중)...", flush=True)
        logged_in = False
        for sec in range(900):
            force_foreground()
            if is_logged_in(ctx, page):
                print(f"🎉 네이버 로그인 감지 성공! (경과: {sec}초)", flush=True)
                logged_in = True
                time.sleep(3.0)
                break
            if sec > 0 and sec % 10 == 0:
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

def main():
    if not CH1_PATH.exists():
        print(f"❌ 파일을 찾을 수 없습니다: {CH1_PATH}")
        sys.exit(1)

    text = CH1_PATH.read_text(encoding="utf-8").strip()
    raw_lines = text.splitlines()

    title = "《크로노스 아르카나》 1장. 카이로스의 침묵"
    paragraphs = []
    
    current_para = []
    for line in raw_lines:
        line_str = line.strip()
        if not line_str:
            if current_para:
                paragraphs.append(" ".join(current_para))
                current_para = []
        elif line_str.startswith("※") or line_str.startswith("《크로노스"):
            continue
        else:
            current_para.append(line_str)
            
    if current_para:
        paragraphs.append(" ".join(current_para))

    tags = ["크로노스아르카나", "SF소설", "미스터리소설", "웹소설", "연재소설", "타임루프", "추리소설"]

    print("=" * 65, flush=True)
    print("🚀 [네이버 블로그 100% 무인 전자동 발행 엔진 가동]", flush=True)
    print(f"📌 제목: {title}", flush=True)
    print(f"📄 본문 단락 수: {len(paragraphs)}개", flush=True)
    print(f"🏷️ 태그 수: {len(tags)}개", flush=True)
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

        # 1. 로그인 세션 확인 및 QR 창 최상단 노출
        ensure_session(ctx, page)

        # 2. 스마트에디터 진입
        if "Redirect=Write" not in page.url and "PostWriteForm" not in page.url and "postwrite" not in page.url:
            print("스마트에디터 작성 페이지로 진입 중...", flush=True)
            page.goto("https://blog.naver.com/kwonflower58?Redirect=Write&", wait_until="domcontentloaded", timeout=60000)
        time.sleep(5.0)

        # 3. 에디터 프레임 탐색
        print("에디터 프레임 탐색 및 팝업 정리 중...", flush=True)
        mf = find_editor_frame(page, timeout_sec=40)
        dismiss_editor_popups(mf)

        # 4. 제목 자동 입력
        print(f"✍️ 제목 입력 중: {title}", flush=True)
        title_box = mf.locator(".se-documentTitle .se-ff-nanumgothic, .se-documentTitle input, .se-documentTitle [contenteditable='true']").first
        title_box.click()
        time.sleep(0.5)
        page.keyboard.insert_text(title)
        time.sleep(0.5)

        # 5. 본문 문단 자동 작성
        print("✍️ 본문 자동 타이핑 작성 중...", flush=True)
        bl = mf.locator(".se-component.se-text .se-text-paragraph").first
        bl.click()
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
        print("✔ 본문 작성 완료!", flush=True)

        # 6. 우측 상단 [발행] 설정 열기
        print("⚙️ [발행] 설정 패널 여는 중...", flush=True)
        mf.get_by_role("button", name="발행").first.click()
        time.sleep(2.0)

        # 7. 태그 자동 입력
        if tags:
            print(f"🏷️ 태그 {len(tags)}개 자동 입력 중...", flush=True)
            tag_box = mf.get_by_role("combobox", name=re.compile(r"^태그"))
            if tag_box.count() > 0:
                tag_box.first.click()
            else:
                mf.locator('input[placeholder*="태그"], [aria-label*="태그"], [id*="tag-input"]').first.click()

            for tg in tags[:10]:
                page.keyboard.insert_text(tg)
                page.keyboard.press("Enter")
                time.sleep(0.15)
            print("✔ 태그 입력 완료!", flush=True)

        # 8. 전체공개 설정 확인
        try:
            mf.locator('label[for="open_all"], input#open_all, label:has-text("전체공개")').first.click()
            time.sleep(0.4)
        except Exception:
            pass

        # 9. 최종 [발행] 버튼 클릭
        print("🚀 최종 [발행] 버튼 클릭 중...", flush=True)
        mf.get_by_role("button", name="발행").last.click()
        time.sleep(6.0)

        print("\n" + "=" * 65, flush=True)
        print("🎉 [완벽 성공!] 《크로노스 아르카나》 1장이 네이버 블로그에 성공적으로 발행되었습니다!", flush=True)
        print("=" * 65 + "\n", flush=True)

        time.sleep(3)
        page.close()
        ctx.close()

if __name__ == "__main__":
    main()
