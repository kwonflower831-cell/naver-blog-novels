import os
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

PROFILE_DIR = r"C:\Users\kwonf\.gemini\antigravity\scratch\chrome-naver-profile"
ARTIFACT_DIR = Path(r"C:\Users\kwonf\.gemini\antigravity\brain\c285795c-7c15-43e5-b14b-c9be4328a60d")
QR_PATH = ARTIFACT_DIR / "naver_qr.png"

def is_logged_in(ctx, page):
    cookies = ctx.cookies()
    has_auth = any(c.get("name") in ("NID_AUT", "NID_SES") for c in cookies)
    if has_auth:
        return True
    u = page.url.lower()
    return "nidlogin" not in u and "nid.naver.com" not in u and ("blog.naver.com" in u or "postwrite" in u)

def main():
    print("=" * 60)
    print("📸 [실제 네이버 QR코드 화면 전환 & 캡처]")
    print("=" * 60)

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_DIR,
            channel="chrome",
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()

        print("1. 네이버 로그인 페이지 접속 중...")
        page.goto("https://nid.naver.com/nidlogin.login?url=https%3A%2F%2Fblog.naver.com%2Fkwonflower58", wait_until="domcontentloaded", timeout=30000)
        time.sleep(1.5)

        # 'QR sign-in' 또는 'QR코드' 링크 클릭
        print("2. QR코드 탭으로 전환 중...")
        qr_btn = page.locator("a:has-text('QR'), button:has-text('QR'), .menu_id_qr, a[href*='qrcode']").first
        if qr_btn.count() > 0:
            qr_btn.click()
            time.sleep(2.0)
        else:
            page.goto("https://nid.naver.com/nidlogin.login?mode=qrcode&url=https%3A%2F%2Fblog.naver.com%2Fkwonflower58", wait_until="domcontentloaded")
            time.sleep(2.0)

        # 실제 QR코드 화면 캡처
        print(f"3. 실제 QR코드 캡처 저장: {QR_PATH}")
        page.screenshot(path=str(QR_PATH))
        print("✔ 진짜 QR코드 캡처 완료!")

        # 스마트폰 스캔 대기 (최대 180초)
        print("4. 스마트폰 네이버 앱 스캔 대기 중 (180초)...")
        logged_in = False
        for sec in range(180):
            if is_logged_in(ctx, page):
                print(f"🎉 [로그인 감지 성공!] ({sec}초 경과)")
                logged_in = True
                time.sleep(3.0)
                break
            time.sleep(1.0)
            if sec > 0 and sec % 10 == 0:
                print(f"   스캔 대기 중... ({sec}초)")

        if not logged_in:
            print("❌ 시간 초과")
            sys.exit(1)

        print("✅ 네이버 로그인 세션 영구 보존 완료!")
        ctx.close()

if __name__ == "__main__":
    main()
