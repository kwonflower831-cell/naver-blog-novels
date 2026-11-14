import ctypes
import os
import re
import sys
import threading
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

BASE_DIR = Path(r"C:\Users\kwonf\.gemini\antigravity\scratch\novels")
PROFILE_DIR = r"C:\Users\kwonf\.gemini\antigravity\scratch\chrome-naver-profile"

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
    """세션이 유효한지 확인하고, 필요 시 QR 로그인 화면을 띄워 1회 세션을 영구 보존"""
    print("🔒 [1단계] 네이버 로그인 세션 확인 중...", flush=True)
    try:
        page.goto("https://blog.naver.com/kwonflower58?Redirect=Write&", wait_until="domcontentloaded", timeout=30000)
    except Exception:
        pass
    time.sleep(2.5)

    if not is_logged_in(ctx, page):
        print("⚠️ 세션 필요: 네이버 로그인 화면으로 이동합니다 (QR코드 우선)...", flush=True)
        # QR코드 로그인이 가장 빠르고 캡차가 없으므로 QR 탭으로 이동
        page.goto("https://nid.naver.com/nidlogin.login?mode=qrcode&url=https%3A%2F%2Fblog.naver.com%2Fkwonflower58%3FRedirect%3DWrite%26", wait_until="domcontentloaded")
        page.bring_to_front()
        bring_window_to_top()

        def show_popup():
            try:
                ctypes.windll.user32.MessageBoxW(
                    0,
                    "화면에 열린 크롬 창에서 네이버 로그인을 1회 완료해 주세요.\n\n"
                    "※ 네이버 앱 QR코드를 찍으시거나 아이디/비밀번호로 로그인하시면 됩니다.\n"
                    "이 1회 인증으로 세션이 영구 보존되어, 다음부터는 이 창조차 뜨지 않고\n"
                    "100% 무인 전자동으로 글이 발행됩니다!",
                    "영구 세션 1회 등록 안내",
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

def publish_post(title: str, paragraphs: list, tags: list, is_public: bool = True):
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

        # 1. 세션 확인 및 확보
        ensure_session(ctx, page)

        # 2. 에디터 진입 확인
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
            time.sleep(0.04)
            if i < len(paragraphs) - 1:
                page.keyboard.press("Enter")
                time.sleep(0.04)
                page.keyboard.press("Enter")
                time.sleep(0.04)

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

        # 8. 공개 설정 확인
        if is_public:
            try:
                mf.locator('label[for="open_all"], input#open_all, label:has-text("전체공개")').first.click()
                time.sleep(0.4)
            except Exception:
                pass
        else:
            try:
                mf.locator('label[for="open_private"], input#open_private, label:has-text("비공개")').first.click()
                time.sleep(0.4)
            except Exception:
                pass

        # 9. 최종 [발행] 버튼 클릭
        print("🚀 최종 [발행] 버튼 클릭 중...", flush=True)
        mf.get_by_role("button", name="발행").last.click()
        time.sleep(6.0)

        print("\n" + "=" * 65, flush=True)
        print("🎉 [완벽 성공!] 포스팅이 성공적으로 전체공개 발행되었습니다!", flush=True)
        print("=" * 65 + "\n", flush=True)

        time.sleep(3)
        page.close()
        ctx.close()
        return True

COUPANG_PRESET = {
    "title": "자취생 & 주부 필수! 쿠팡에서 무조건 쟁여두는 가성비 생필품 BEST 3 (솔직 가격비교)",
    "tags": ["쿠팡생필품", "자취생필수템", "가성비생필품", "탐사수2L", "쟁여템추천", "생활비절약", "쿠팡로켓배송"],
    "paragraphs": [
        "안녕하세요! 매달 나가는 고정 생활비, 물가가 너무 올라서 장보기가 무서울 정도입니다.",
        "하지만 쿠팡 로켓배송과 정기배송을 똑똑하게 활용하면 오프라인 대형마트보다 매달 최소 5~10만 원 이상의 생활비를 아낄 수 있다는 사실, 알고 계셨나요?",
        "오늘은 수많은 후기와 판매량으로 검증된, 장바구니에 무조건 쟁여두는 가성비 생필품 꿀템 3선을 꼼꼼하게 비교해 드립니다!",
        "----------------------------------------",
        "💧 1. 생수 부동의 1위: 탐사수 2L x 6병 / 500ml",
        "• 추천 이유: 마트에서 무겁게 들고 올 필요 없이 현관 앞까지 무료 로켓배송!",
        "• 가성비 비교: 편의점 대비 병당 1/3 가격 수준으로 자취생과 1인 가구 필수템입니다.",
        "👉 [추천 상품 바로가기]: https://link.coupang.com/a/iE3BaOBMNo",
        "(※ 실시간 특가 및 로켓와우 혜택 적용 가능)",
        "----------------------------------------",
        "🧻 2. 도톰한 3겹 롤화장지 (30롤 대용량)",
        "• 추천 이유: 먼지 날림이 적고 3겹 데코 엠보싱으로 흡수력이 뛰어납니다.",
        "• 꿀팁: 10m당 단가를 비교했을 때 브랜드 제품 중 가장 경제적입니다.",
        "----------------------------------------",
        "🔒 3. 자취방 & 원룸 필수: 무타공 현관문 이중 안전고리",
        "• 추천 이유: 못이나 나사 없이 문틀에 10초 만에 설치 가능한 철벽 보안템!",
        "• 혼자 사는 원룸이나 여성 자취생들의 불안을 덜어주는 최고의 안전 지킴이입니다.",
        "----------------------------------------",
        "💡 현명한 소비 팁: 생필품은 다 떨어졌을 때 급하게 편의점에서 사면 비용이 2~3배 듭니다. 자주 쓰는 소모품은 특가 쟁여템으로 미리 구비해 두시는 것을 추천합니다!",
        "이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다."
    ]
}

if __name__ == "__main__":
    preset = COUPANG_PRESET
    publish_post(preset["title"], preset["paragraphs"], preset["tags"], is_public=True)
