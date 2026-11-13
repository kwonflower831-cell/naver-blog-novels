import sys
import time
from playwright.sync_api import sync_playwright

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

PROFILE_DIR = r"C:\Users\kwonf\.gemini\antigravity\scratch\chrome-naver-profile"

def main():
    print("브라우저를 실행합니다...", flush=True)
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_DIR,
            channel="chrome",
            headless=False,
            args=["--start-maximized", "--disable-blink-features=AutomationControlled"],
            no_viewport=True,
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()

        print("네이버 블로그 카테고리 관리 페이지로 이동 중...", flush=True)
        page.goto("https://admin.blog.naver.com/kwonflower58/category", wait_until="domcontentloaded")
        time.sleep(4)

        if "nid.naver.com" in page.url:
            print("로그인이 필요합니다. 브라우저에서 네이버 로그인을 1회 완료해 주세요 (대기 중)...", flush=True)
            for _ in range(600):
                if "nid.naver.com" not in page.url and "admin.blog.naver.com" in page.url:
                    print("로그인 확인 완료!", flush=True)
                    time.sleep(2)
                    break
                time.sleep(1)

        print("현재 URL:", page.url, flush=True)
        time.sleep(3)

        # 생활용품 가격비교 카테고리 찾기
        print("카테고리 목록에서 '생활용품 가격비교' 탐색 중...", flush=True)
        try:
            # 카테고리 이름 요소 클릭
            cat_elem = page.locator('text="생활용품 가격비교"').first
            if cat_elem.count() > 0 and cat_elem.is_visible():
                print("생활용품 가격비교 카테고리 발견! 클릭합니다.", flush=True)
                cat_elem.click()
                time.sleep(1.5)

                # 비공개 라디오 버튼 찾기
                # 보통 id="openRadio2" or name="openRadio" or label contains "비공개"
                private_radio = page.locator('input[type="radio"][value="false"], input#openRadio2, label:has-text("비공개")')
                if private_radio.count() > 0:
                    print("비공개 라디오 버튼 클릭...", flush=True)
                    private_radio.first.click()
                    time.sleep(1.0)

                # 확인 버튼 누르기
                save_btn = page.locator('button:has-text("확인"), input[type="submit"][value="확인"], .btn_apply button, #submitButton')
                for idx in range(save_btn.count()):
                    b = save_btn.nth(idx)
                    if b.is_visible():
                        print(f"확인 버튼({idx}) 클릭...", flush=True)
                        b.click()
                        time.sleep(2.0)
                        break

                print("생활용품 가격비교 카테고리 비공개 설정 완료!", flush=True)
            else:
                print("생활용품 가격비교 카테고리를 찾을 수 없습니다. (이미 비공개이거나 이름이 다를 수 있음)", flush=True)
        except Exception as e:
            print("카테고리 비공개 설정 중 오류:", e, flush=True)

        # 글 관리 페이지로 이동해서 cat 1의 상품 글들도 비공개 처리 시도
        print("\n글 관리 메뉴로 이동을 시도합니다...", flush=True)
        page.goto("https://admin.blog.naver.com/kwonflower58/postmanage", wait_until="domcontentloaded")
        time.sleep(3)
        print("글 관리 URL:", page.url, flush=True)

        time.sleep(5)
        page.close()
        ctx.close()
        print("작업 완료!", flush=True)

if __name__ == "__main__":
    main()
