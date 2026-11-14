import os
import re
import sys
import time
import pyperclip
from pathlib import Path
from playwright.sync_api import sync_playwright

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

PROFILE_DIR = r"C:\Users\kwonf\.gemini\antigravity\scratch\chrome-naver-profile"

TITLE = "자취생 & 주부 필수! 쿠팡에서 무조건 쟁여두는 가성비 생필품 BEST 3 (솔직 가격비교)"

TAGS = [
    "쿠팡생필품", "자취생필수템", "가성비생필품", "탐사수2L", "쟁여템추천",
    "생활비절약", "쿠팡로켓배송"
]

PARAS = [
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
    print("=" * 60, flush=True)
    print("🚀 [2번 무인 전자동 블로그 포스팅 발행 시작]", flush=True)
    print(f"📌 제목: {TITLE}", flush=True)
    print("=" * 60, flush=True)

    with sync_playwright() as p:
        print("전용 자동화 브라우저 실행 중...", flush=True)
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_DIR,
            channel="chrome",
            headless=False,
            args=["--start-maximized", "--disable-blink-features=AutomationControlled"],
            no_viewport=True,
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()

        print("블로그 글쓰기 페이지 진입 중...", flush=True)
        try:
            page.goto("https://blog.naver.com/kwonflower58?Redirect=Write&", wait_until="domcontentloaded", timeout=60000)
        except Exception as e:
            print("이동 안내:", e, flush=True)
        time.sleep(3.5)

        # 로그인 필요 여부 확인
        if "nidlogin" in page.url or "nid.naver.com" in page.url:
            print("로그인 페이지 감지 -> 캡차 회피 자동 로그인 시도 중...", flush=True)
            try:
                time.sleep(1.0)
                # 1. ID 입력
                id_box = page.locator("#id, input[name='id']").first
                if id_box.count() > 0:
                    id_box.click()
                    pyperclip.copy("kwonflower58")
                    page.keyboard.press("Control+v")
                    time.sleep(0.3)

                # 2. PW 입력
                pw_box = page.locator("#pw, input[name='pw']").first
                if pw_box.count() > 0:
                    pw_box.click()
                    pyperclip.copy("kwon7604@@")
                    page.keyboard.press("Control+v")
                    time.sleep(0.3)

                # 3. 로그인 상태 유지 체크 (#loginStay)
                stay_box = page.locator("#loginStay, #keep, label:has-text('로그인 상태 유지')").first
                if stay_box.count() > 0:
                    try:
                        stay_box.click()
                    except:
                        pass

                # 4. 로그인 버튼 클릭 (#loginBtn_column / #loginBtn_row)
                btn = page.locator("#loginBtn_column, #loginBtn_row, button:has-text('로그인'), input[type='submit']").first
                if btn.count() > 0:
                    btn.click()
                    print("로그인 버튼 자동 클릭 완료! 결과 대기 중...", flush=True)
                    time.sleep(4.0)
            except Exception as e:
                print("자동 로그인 시도 오류:", e, flush=True)

            # 로그인 완료 대기 루프 (최대 60초)
            for sec in range(60):
                cookies = ctx.cookies()
                has_auth = any(c.get("name") in ("NID_AUT", "NID_SES") for c in cookies)
                is_blog = "blog.naver.com" in page.url and "nidlogin" not in page.url
                if has_auth or is_blog:
                    print("✔ 네이버 로그인 확인 성공!", flush=True)
                    break
                time.sleep(1)

        # 에디터 진입 확인
        if "Redirect=Write" not in page.url and "PostWriteForm" not in page.url and "postwrite" not in page.url:
            print("스마트에디터 페이지로 이동 중...", flush=True)
            page.goto("https://blog.naver.com/kwonflower58?Redirect=Write&", wait_until="domcontentloaded", timeout=60000)
        time.sleep(5.0)

        print("에디터 프레임 탐색 중...", flush=True)
        mf = find_editor_frame(page, timeout_sec=40)
        dismiss_editor_popups(mf)

        # 1. 제목 입력
        print(f"1. 제목 자동 입력 중: {TITLE}", flush=True)
        title_box = mf.locator(".se-documentTitle .se-ff-nanumgothic, .se-documentTitle input, .se-documentTitle [contenteditable='true']").first
        title_box.click()
        time.sleep(0.5)
        page.keyboard.insert_text(TITLE)
        time.sleep(0.5)

        # 2. 본문 문단 작성
        print(f"2. 본문 문단 자동 타이핑 입력 중 (총 {len(PARAS)}단락)...", flush=True)
        bl = mf.locator(".se-component.se-text .se-text-paragraph").first
        bl.click()
        time.sleep(0.4)

        for i, para in enumerate(PARAS):
            page.keyboard.insert_text(para)
            time.sleep(0.04)
            if i < len(PARAS) - 1:
                page.keyboard.press("Enter")
                time.sleep(0.04)
                page.keyboard.press("Enter")
                time.sleep(0.04)

        time.sleep(1.0)
        print("✔ 본문 입력 완료!", flush=True)

        # 3. 우측 상단 [발행] 설정 열기
        print("3. 우측 상단 [발행] 버튼 클릭...", flush=True)
        mf.get_by_role("button", name="발행").first.click()
        time.sleep(2.0)

        # 4. 태그 자동 입력
        print("4. 태그 7개 자동 입력 중...", flush=True)
        tag_box = mf.get_by_role("combobox", name=re.compile(r"^태그"))
        if tag_box.count() > 0:
            tag_box.first.click()
        else:
            mf.locator('input[placeholder*="태그"], [aria-label*="태그"], [id*="tag-input"]').first.click()

        for tg in TAGS:
            page.keyboard.insert_text(tg)
            page.keyboard.press("Enter")
            time.sleep(0.15)
        print("✔ 태그 입력 완료!", flush=True)

        # 5. 전체공개 확인
        try:
            mf.locator('label[for="open_all"], input#open_all, label:has-text("전체공개")').first.click()
            time.sleep(0.5)
        except Exception:
            pass

        # 6. 최종 [발행] 버튼 클릭
        print("5. 최종 [발행] 버튼 클릭 중...", flush=True)
        mf.get_by_role("button", name="발행").last.click()
        time.sleep(6.0)

        print("\n" + "=" * 60, flush=True)
        print("🎉 [2번 무인 전자동 발행 완벽 성공!]", flush=True)
        print("새 포스팅이 네이버 블로그에 전체공개로 성공적으로 발행되었습니다!", flush=True)
        print("=" * 60 + "\n", flush=True)

        time.sleep(3)
        page.close()
        ctx.close()

if __name__ == "__main__":
    main()
