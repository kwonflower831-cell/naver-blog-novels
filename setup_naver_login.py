import ctypes
import os
import sys
import threading
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

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

def setup_permanent_session():
    print("=" * 60, flush=True)
    print("🚀 [Aside 스타일 영구 로그인 세팅 시작]", flush=True)
    print(f"📁 전용 프로필 디렉토리: {PROFILE_DIR}", flush=True)
    print("=" * 60, flush=True)

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_DIR,
            channel="chrome",
            headless=False,
            args=["--start-maximized", "--disable-blink-features=AutomationControlled"],
            no_viewport=True,
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()

        print("네이버 로그인 페이지로 이동 중...", flush=True)
        page.goto("https://nid.naver.com/nidlogin.login?url=https%3A%2F%2Fblog.naver.com%2Fkwonflower58", wait_until="domcontentloaded")
        page.bring_to_front()
        bring_window_to_top()

        # '로그인 상태 유지' 체크박스 자동 활성화
        try:
            page.evaluate("""() => {
                const keep = document.querySelector('#keep');
                if (keep && !keep.checked) {
                    keep.click();
                }
                const b = document.createElement('div');
                b.id = 'session-banner';
                b.style.cssText = 'position:fixed;top:15px;left:50%;transform:translateX(-50%);z-index:9999999;background:#ffffff;border:3px solid #03c75a;border-radius:12px;box-shadow:0 8px 24px rgba(0,0,0,0.25);padding:16px 32px;text-align:center;font-family:sans-serif;pointer-events:none;';
                b.innerHTML = '<div style=\"font-size:18px;font-weight:bold;color:#03c75a;margin-bottom:6px;\">🔒 [1회 영구 로그인 세팅]</div><div style=\"font-size:14px;color:#222;\">이 창에서 <b>1회 로그인</b>을 완료하시면,<br>앞으로는 로그인 없이 <b>Aside처럼 전자동으로 즉시 글이 발행</b>됩니다!</div>';
                document.body.prepend(b);
            }""")
            print("✔ '로그인 상태 유지' 옵션을 자동으로 체크했습니다.", flush=True)
        except Exception as e:
            print("배너 표시 안내:", e, flush=True)

        def show_popup():
            try:
                ctypes.windll.user32.MessageBoxW(
                    0,
                    "화면에 열린 크롬 창에서 네이버 로그인을 1회만 완료해 주세요.\n\n"
                    "※ '로그인 상태 유지'가 자동 적용되어 있으므로\n"
                    "이번 1회만 로그인하시면 앞으로는 로그인 과정 없이\n"
                    "Aside처럼 모든 글이 원클릭 100% 전자동으로 발행됩니다!\n\n"
                    "(아이디/비밀번호 또는 네이버 앱 QR코드 모두 가능)",
                    "Aside 스타일 영구 로그인 세팅 (1회 한정)",
                    0x40 | 0x10000
                )
            except Exception:
                pass
        threading.Thread(target=show_popup, daemon=True).start()

        print("사용자 로그인 완료 대기 중...", flush=True)
        logged_in = False
        for sec in range(900):
            cookies = ctx.cookies()
            has_auth = any(c.get("name") in ("NID_AUT", "NID_SES") for c in cookies)
            is_blog = "blog.naver.com" in page.url and "nidlogin" not in page.url
            if has_auth or is_blog:
                print(f"\n🎉 로그인 성공 감지! (경과 시간: {sec}초)", flush=True)
                logged_in = True
                time.sleep(3.0)
                break
            if sec > 0 and sec % 15 == 0:
                print(f"로그인 대기 중 ({sec}초 경과)...", flush=True)
            time.sleep(1)

        if not logged_in:
            print("로그인 대기 시간이 초과되었습니다.", flush=True)
            page.close()
            ctx.close()
            return False

        print("영구 세션 쿠키 저장 완료! 검증을 시작합니다...", flush=True)
        time.sleep(2)
        page.close()
        ctx.close()

    # 무음 검증
    print(" headless 모드에서 세션 유효성 자동 검증 중...", flush=True)
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_DIR,
            channel="chrome",
            headless=True
        )
        page = ctx.new_page()
        page.goto("https://blog.naver.com/kwonflower58?Redirect=Write&", wait_until="domcontentloaded")
        time.sleep(3)
        u = page.url.lower()
        if "nidlogin" not in u and ("postwrite" in u or "redirect=write" in u or "blog.naver.com" in u):
            print("\n" + "=" * 60, flush=True)
            print("✅ [검증 성공] 영구 세션이 완벽하게 등록되었습니다!", flush=True)
            print("이제 앞으로 어떤 글이든 로그인 창 없이 즉시 100% 전자동 발행됩니다.", flush=True)
            print("=" * 60 + "\n", flush=True)
            ctx.close()
            return True
        else:
            print("세션 재검증 필요 URL:", page.url, flush=True)
            ctx.close()
            return False

if __name__ == "__main__":
    setup_permanent_session()
