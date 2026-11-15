"""
포스타입(Postype) 전자동 무인 발행 엔진 (Playwright 기반)

- AI 토큰 소모: 0 (로컬 파이썬 프로세스 직접 구동)
- 최초 1회 브라우저 로그인 세션을 영구 보존하여 이후 100% 무인 발행
- 소설 텍스트 파일(ch*-published.txt) 자동 파싱, 제목/부제/본문/시리즈/태그/유무료 설정 지원
"""

import argparse
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
PROFILE_DIR = r"C:\Users\kwonf\.gemini\antigravity\scratch\chrome-postype-profile"
DEFAULT_CHANNEL = "kwonflower-story"

# 소설별 기본 메타데이터 매핑
NOVEL_METADATA = {
    "silence": {
        "name": "침묵의 방",
        "folder": "novel-silence-text",
        "series": "침묵의 방",
        "tags": ["스릴러", "미스터리", "추리소설", "폐쇄병동", "침묵의방"]
    },
    "evidence4": {
        "name": "증거물 4호",
        "folder": "novel-evidence4-text",
        "series": "증거물 4호",
        "tags": ["스릴러", "미스터리", "추리소설", "경찰소설", "증거물4호"]
    },
    "checkout": {
        "name": "체크아웃 11:00",
        "folder": "novel-checkout-text",
        "series": "체크아웃 11:00",
        "tags": ["스릴러", "미스터리", "추리소설", "단편소설", "밀실"]
    },
    "yupum": {
        "name": "유품",
        "folder": "novel-yupum-text",
        "series": "유품",
        "tags": ["스릴러", "미스터리", "추리소설", "유품정리사", "유품"]
    },
    "lasttalk": {
        "name": "마지막 통화",
        "folder": "novel-lasttalk-text",
        "series": "마지막 통화",
        "tags": ["스릴러", "미스터리", "추리소설", "마지막통화"]
    }
}

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
                    if "포스타입" in title or "POSTYPE" in title or "Chrome" in title:
                        user32.ShowWindow(hwnd, 3) # SW_MAXIMIZE
                        user32.SetForegroundWindow(hwnd)
            return True
        user32.EnumWindows(WNDENUMPROC(enum_cb), 0)
    except Exception:
        pass

def is_logged_in(ctx, page):
    """포스타입 로그인 상태 확인"""
    try:
        u = page.url.lower()
        # 로그인 진행 중인 페이지(소셜 인증 포함)에서는 아직 미완료
        auth_keywords = ["postype.com/login", "nid.naver.com", "accounts.kakao.com", "accounts.google.com", "appleid.apple.com"]
        if any(k in u for k in auth_keywords):
            return False

        if "postype.com" in u and "login" not in u:
            # DOM 요소 판정: 스튜디오/알림/프로필/에디터 등이 있거나 '로그인' 버튼이 사라진 경우
            has_studio = page.locator("a[href*='/studio'], a[href*='/editor'], button[aria-label*='알림'], [aria-label*='프로필'], img[alt*='프로필']").count() > 0
            has_login = page.locator("a[href*='/login'], button:has-text('로그인')").count() > 0
            if has_studio or (not has_login and "postype.com" in u):
                return True
    except Exception:
        pass
    return False

def ensure_session(ctx, page):
    """포스타입 세션을 확인하고, 미로그인 시 팝업을 띄워 1회 로그인 대기"""
    print("🔒 [1단계] 포스타입 로그인 세션 확인 중...", flush=True)
    try:
        page.goto("https://www.postype.com/", wait_until="domcontentloaded", timeout=30000)
    except Exception:
        pass
    time.sleep(2.0)

    if not is_logged_in(ctx, page):
        print("⚠️ 로그인 필요: 포스타입 로그인 화면으로 이동합니다...", flush=True)
        page.goto("https://www.postype.com/login", wait_until="domcontentloaded")
        page.bring_to_front()
        bring_window_to_top()

        def show_popup():
            try:
                ctypes.windll.user32.MessageBoxW(
                    0,
                    "화면에 열린 크롬 창에서 포스타입 로그인을 1회 완료해 주세요.\n\n"
                    "※ 카카오, 네이버, 구글, 이메일 등 편하신 방식으로 로그인하시면 됩니다.\n"
                    "이 1회 인증으로 세션이 영구 보존되어, 다음부터는 로그인 창 없이\n"
                    "100% 무인 전자동으로 글이 발행됩니다!",
                    "포스타입 영구 세션 1회 등록 안내",
                    0x40 | 0x10000
                )
            except Exception:
                pass
        threading.Thread(target=show_popup, daemon=True).start()

        print("👉 화면의 브라우저에서 포스타입 로그인을 완료해 주세요 (대기 중)...", flush=True)
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
            raise RuntimeError("포스타입 로그인 대기 시간 초과")

    print("✅ [세션 정상] 포스타입 로그인 세션이 확인되었습니다!", flush=True)

def parse_novel_file(file_path: Path):
    """소설 파일에서 제목과 본문을 추출"""
    text = file_path.read_text(encoding="utf-8").strip()
    lines = text.splitlines()
    
    title = ""
    start_idx = 0
    
    # 첫머리에서 제목 추출
    for i, line in enumerate(lines[:5]):
        s = line.strip()
        if s.startswith("《") or "화." in s or "장." in s:
            title = s
            start_idx = i + 1
            break
            
    if not title:
        # 파일명 기반 추론
        title = file_path.stem

    body = "\n".join(lines[start_idx:]).strip()
    return title, body

def publish_to_postype(
    title: str,
    body: str,
    channel: str = DEFAULT_CHANNEL,
    series: str = "",
    subtitle: str = "",
    tags: list = None,
    price: int = 0,
    dry_run: bool = False
):
    """포스타입에 단일 포스트 전자동 발행"""
    if tags is None:
        tags = []

    print("=" * 65, flush=True)
    print("🚀 [포스타입 100% 무인 전자동 발행 엔진 가동]", flush=True)
    print(f"📌 채널: @{channel}", flush=True)
    print(f"📌 제목: {title}", flush=True)
    if series:
        print(f"📚 시리즈: {series}", flush=True)
    if subtitle:
        print(f"📝 부제: {subtitle}", flush=True)
    print(f"🏷️ 태그: {', '.join(tags)}", flush=True)
    print(f"💰 포인트 설정: {'무료' if price == 0 else f'{price}P'}", flush=True)
    print(f"📄 본문 길이: {len(body)} 자", flush=True)
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

        # 1. 로그인 세션 확인 및 확보
        ensure_session(ctx, page)

        # 2. 에디터 진입
        editor_url = f"https://www.postype.com/editor/{channel}/normal"
        print(f"✍️ 에디터 페이지로 이동 중: {editor_url}", flush=True)
        page.goto(editor_url, wait_until="domcontentloaded", timeout=45000)
        time.sleep(2.5)

        # 3. 제목 입력
        print("✍️ 제목 입력 중...", flush=True)
        title_input = page.getByPlaceholder("제목을 입력하세요.", exact=False).first
        if not title_input.is_visible():
            title_input = page.locator("input[placeholder*='제목'], textarea[placeholder*='제목']").first
        title_input.click()
        time.sleep(0.3)
        title_input.fill(title)
        time.sleep(0.5)

        # 4. 부제 입력 (있는 경우)
        if subtitle:
            subtitle_input = page.getByPlaceholder("부제를 입력하세요.", exact=False).first
            if subtitle_input.is_visible():
                print("✍️ 부제 입력 중...", flush=True)
                subtitle_input.click()
                subtitle_input.fill(subtitle)
                time.sleep(0.3)

        # 5. 본문 입력
        print("✍️ 본문 입력 중...", flush=True)
        editor = page.locator("div[contenteditable='true']").first
        editor.click()
        time.sleep(0.3)
        editor.fill(body)
        time.sleep(1.0)

        # 6. 상단 '발행' 버튼 클릭 (설정 모달/사이드바 열기)
        print("⚙️ 발행 설정 패널 여는 중...", flush=True)
        publish_btn = page.getByRole("button", { "name": "발행", "exact": True }).first
        publish_btn.click()
        time.sleep(1.5)

        # 7. 시리즈 선택 (지정된 경우)
        if series:
            try:
                print(f"📚 시리즈 '{series}' 지정 중...", flush=True)
                series_combo = page.getByRole("combobox", { "name": "시리즈" })
                if not series_combo.is_visible():
                    series_combo = page.locator("button:has-text('시리즈 선택'), [aria-label*='시리즈']").first
                if series_combo.is_visible():
                    series_combo.click()
                    time.sleep(0.5)
                    series_opt = page.getByRole("option", { "name": series, "exact": False }).first
                    if not series_opt.is_visible():
                        series_opt = page.locator(f"[role='option']:has-text('{series}'), li:has-text('{series}')").first
                    if series_opt.is_visible():
                        series_opt.click()
                        time.sleep(0.5)
                        print(f"  ✓ 시리즈 '{series}' 연결 완료")
            except Exception as e:
                print(f"  ⚠️ 시리즈 선택 중 경고 (무시 가능): {e}", flush=True)

        # 8. 태그 추가
        if tags:
            print("🏷️ 태그 등록 중...", flush=True)
            for tag in tags:
                try:
                    tag_btn = page.getByRole("button", { "name": tag, "exact": True })
                    if tag_btn.is_visible():
                        tag_btn.click()
                        time.sleep(0.2)
                    else:
                        tag_input = page.getByPlaceholder("태그 입력", exact=False).first
                        if tag_input.is_visible():
                            tag_input.fill(tag)
                            page.keyboard.press("Enter")
                            time.sleep(0.2)
                except Exception:
                    pass

        # 9. 유료 포인트 설정 (price > 0 인 경우)
        if price > 0:
            print(f"💰 유료 포인트 설정 ({price}P)...", flush=True)
            try:
                paid_radio = page.locator("label:has-text('유료'), input[value='PAID']").first
                if paid_radio.is_visible():
                    paid_radio.click()
                    time.sleep(0.3)
                price_input = page.locator("input[placeholder*='포인트'], input[type='number']").first
                if price_input.is_visible():
                    price_input.fill(str(price))
                    time.sleep(0.3)
            except Exception as e:
                print(f"  ⚠️ 포인트 설정 경고: {e}", flush=True)

        # 10. 최종 발행하기 버튼 클릭
        if dry_run:
            print("🧪 [Dry-run 모드] 최종 발행 버튼을 누르지 않고 중단합니다.", flush=True)
            time.sleep(5)
            ctx.close()
            return None

        print("🚀 [최종 발행] '발행하기' 버튼 클릭 중...", flush=True)
        submit_btn = page.getByRole("button", { "name": "발행하기" }).first
        if not submit_btn.is_visible():
            submit_btn = page.locator("button:has-text('발행하기')").last
        submit_btn.click()

        # 11. 발행 완료 대기 및 URL 캡처
        print("⏳ 발행 완료 처리 대기 중...", flush=True)
        time.sleep(4.0)
        page.wait_for_load_state("load", timeout=30000)

        current_url = page.url
        post_url = ""

        # 완료 화면에서 링크 복사 또는 포스트 바로가기 추출
        match = re.search(r"/normal/(\d+)/completed", current_url)
        if match:
            post_id = match.group(1)
            post_url = f"https://www.postype.com/@{channel}/post/{post_id}"
        elif "/post/" in current_url:
            post_url = current_url
        else:
            view_link = page.locator(f"a[href*='/@{channel}/post/']").first
            if view_link.count() > 0:
                post_url = view_link.get_attribute("href")
                if post_url and not post_url.startswith("http"):
                    post_url = f"https://www.postype.com{post_url}"

        print("=" * 65, flush=True)
        if post_url:
            print("🎉 [발행 대성공!]")
            print(f"🔗 공식 포스트 링크: {post_url}")
        else:
            print(f"✅ 발행 완료! (현재 페이지 URL: {current_url})")
        print("=" * 65, flush=True)

        time.sleep(2.0)
        ctx.close()
        return post_url

def main():
    parser = argparse.ArgumentParser(description="포스타입 100% 무인 전자동 발행 도구")
    parser.add_argument("--novel", choices=list(NOVEL_METADATA.keys()), help="소설 코드 (silence, evidence4, checkout, yupum, lasttalk)")
    parser.add_argument("--ch", type=int, help="회차 번호 (예: 1)")
    parser.add_argument("--file", type=str, help="발행할 텍스트 파일 경로 직접 지정")
    parser.add_argument("--title", type=str, help="포스트 제목 (생략 시 원고 첫 줄에서 자동 추출)")
    parser.add_argument("--subtitle", type=str, default="", help="포스트 부제")
    parser.add_argument("--series", type=str, help="시리즈 이름")
    parser.add_argument("--tags", type=str, help="태그 목록 (쉼표 구분)")
    parser.add_argument("--channel", type=str, default=DEFAULT_CHANNEL, help=f"채널 ID (기본: {DEFAULT_CHANNEL})")
    parser.add_argument("--price", type=int, default=0, help="유료 포인트 (0이면 무료 전체공개)")
    parser.add_argument("--dry-run", action="store_true", help="발행 버튼을 누르지 않는 테스트 모드")
    parser.add_argument("--setup-only", action="store_true", help="발행 없이 로그인 세션만 영구 등록")

    args = parser.parse_args()

    # 로그인 세션만 세팅할 때
    if args.setup_only:
        with sync_playwright() as p:
            ctx = p.chromium.launch_persistent_context(
                user_data_dir=PROFILE_DIR,
                channel="chrome",
                headless=False,
                args=["--start-maximized", "--disable-blink-features=AutomationControlled"],
                no_viewport=True,
            )
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            ensure_session(ctx, page)
            print("✅ 포스타입 로그인 세션 영구 등록이 완료되었습니다!")
            time.sleep(2)
            ctx.close()
        return

    # 파일 및 메타데이터 결정
    target_file = None
    series = args.series or ""
    tags = [t.strip() for t in args.tags.split(",")] if args.tags else []

    if args.novel:
        meta = NOVEL_METADATA[args.novel]
        if not series:
            series = meta["series"]
        if not tags:
            tags = meta["tags"].copy()

        if args.ch:
            folder = BASE_DIR / meta["folder"]
            # chX-published.txt 우선, 없으면 chX-draft.txt
            pub_file = folder / f"ch{args.ch}-published.txt"
            draft_file = folder / f"ch{args.ch}-draft.txt"
            if pub_file.exists():
                target_file = pub_file
            elif draft_file.exists():
                target_file = draft_file
            else:
                print(f"❌ 파일을 찾을 수 없습니다: {pub_file} 또는 {draft_file}")
                sys.exit(1)

    if args.file:
        target_file = Path(args.file)

    if not target_file or not target_file.exists():
        print("❌ 발행할 파일이 지정되지 않았거나 존재하지 않습니다. (--novel + --ch 또는 --file 필요)")
        sys.exit(1)

    print(f"📂 대상 원고 파일: {target_file}")
    file_title, body = parse_novel_file(target_file)
    title = args.title or file_title

    publish_to_postype(
        title=title,
        body=body,
        channel=args.channel,
        series=series,
        subtitle=args.subtitle,
        tags=tags,
        price=args.price,
        dry_run=args.dry_run
    )

if __name__ == "__main__":
    main()
