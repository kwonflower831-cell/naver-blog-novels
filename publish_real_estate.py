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
POST_PATH = BASE_DIR / "content-templates" / "jeonse-protection-kit" / "NAVER_BLOG_전월세계약_특약_체크리스트_포스팅.md"
PROFILE_DIR = r"C:\Users\kwonf\.gemini\antigravity\scratch\chrome-naver-profile"

TITLE = "전월세 계약 전 꼭 봐야 할 안전 체크리스트 & 필수 특약 7선 (무료 서식 배포)"

TAGS = [
    "전세계약체크리스트", "전세사기예방", "전세계약특약", "보증금반환내용증명",
    "최우선변제금", "등기부등본보는법", "깡통전세구별법", "사회초년생자취",
    "원룸계약주의사항", "대항력확보"
]

def load_post_paragraphs():
    raw = POST_PATH.read_text(encoding="utf-8").replace("\r\n", "\n")
    # Extract body between [블로그 본문 시작 ...] and [네이버 블로그 태그 추천 ...]
    start_marker = "[블로그 본문 시작"
    end_marker = "### [네이버 블로그 태그 추천"
    
    start_idx = raw.find(start_marker)
    if start_idx != -1:
        # skip to after the header line
        start_idx = raw.find("\n", start_idx) + 1
        # skip next lines if they are bracket comments or separators
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

def is_logged_in(ctx, page):
    cookies = ctx.cookies()
    nid_cookies = [c['name'] for c in cookies if 'NID' in c['name']]
    if 'NID_AUT' in nid_cookies and 'NID_SES' in nid_cookies:
        return True
    try:
        page.goto("https://blog.naver.com/kwonflower58?Redirect=Write&", timeout=12000, wait_until="domcontentloaded")
        time.sleep(2)
        if "nid.naver.com" not in page.url and ("postwrite" in page.url or "Redirect=Write" in page.url):
            return True
    except Exception:
        pass
    return False

def find_editor_frame(page, timeout_sec=35):
    for _ in range(timeout_sec * 2):
        for f in page.frames:
            try:
                if f.locator(".se-documentTitle").count() > 0 or f.locator(".se-component.se-text .se-text-paragraph").count() > 0:
                    return f
            except Exception:
                pass
        time.sleep(0.5)
    raise RuntimeError(f"Editor frame not found. URL={page.url}")

def dismiss_editor_popups(frame):
    for sel in [".se-popup-button-cancel", ".se-help-panel-close-button"]:
        try:
            btn = frame.locator(sel)
            if btn.count() > 0 and btn.first.is_visible():
                btn.first.click()
                time.sleep(0.5)
        except Exception:
            pass

def publish(is_public=False):
    paras = load_post_paragraphs()
    print(f"Loaded paragraphs count: {len(paras)}")
    print(f"Publish mode: {'전체공개' if is_public else '비공개(검토용)'}")

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_DIR,
            channel="chrome",
            headless=False,
            args=["--start-maximized", "--disable-blink-features=AutomationControlled"],
            no_viewport=True,
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()

        if not is_logged_in(ctx, page):
            print("로그인이 필요합니다. 네이버 로그인 창으로 이동합니다...")
            page.goto("https://nid.naver.com/nidlogin.login?url=https%3A%2F%2Fblog.naver.com%2Fkwonflower58%3FRedirect%3DWrite%26", wait_until="domcontentloaded")
            page.bring_to_front()
            
            # 사용자 로그인 대기
            print("네이버 창에서 로그인을 완료해 주세요 (최대 10분 대기)...")
            logged_in = False
            for _ in range(600):
                if is_logged_in(ctx, page):
                    print("로그인 확인 완료!")
                    logged_in = True
                    time.sleep(2)
                    break
                time.sleep(1)
            if not logged_in:
                raise RuntimeError("로그인 제한 시간 초과")

        print("에디터 진입 중...")
        page.goto("https://blog.naver.com/kwonflower58?Redirect=Write&", wait_until="domcontentloaded")
        time.sleep(5)

        mf = find_editor_frame(page, timeout_sec=35)
        dismiss_editor_popups(mf)

        # 1. 제목 입력
        print("제목 입력 중...")
        title_box = mf.locator(".se-documentTitle .se-ff-nanumgothic, .se-documentTitle input, .se-documentTitle [contenteditable='true']").first
        title_box.click()
        time.sleep(0.5)
        page.keyboard.insert_text(TITLE)
        time.sleep(0.5)

        # 2. 본문 입력
        print("본문 문단 입력 중...")
        bl = mf.locator(".se-component.se-text .se-text-paragraph")
        bl.first.click()
        time.sleep(0.4)

        for i, para in enumerate(paras):
            page.keyboard.insert_text(para)
            time.sleep(0.08)
            if i < len(paras) - 1:
                page.keyboard.press("Enter")
                time.sleep(0.08)
                page.keyboard.press("Enter")
                time.sleep(0.08)

        time.sleep(1.0)
        print("본문 입력 완료!")

        # 3. 발행 패널 열기
        print("발행 패널 여는 중...")
        mf.get_by_role("button", name="발행").first.click()
        time.sleep(1.5)

        # 4. 태그 입력
        print("태그 입력 중...")
        tag_box = mf.get_by_role("combobox", name=re.compile(r"^태그"))
        if tag_box.count() > 0:
            tag_box.first.click()
        else:
            mf.locator('input[placeholder*="태그"], [aria-label*="태그"], [id*="tag-input"]').first.click()
            
        for tg in TAGS[:10]:
            page.keyboard.insert_text(tg)
            page.keyboard.press("Enter")
            time.sleep(0.2)

        # 5. 공개 설정 (전체공개 vs 비공개)
        if not is_public:
            print("비공개 설정 클릭...")
            try:
                mf.locator('label[for="open_private"], input#open_private, label:has-text("비공개")').first.click()
                time.sleep(0.5)
            except Exception as e:
                print("비공개 클릭 실패(기본값 유지):", e)

        # 6. 최종 발행 클릭
        print("최종 발행 버튼 클릭...")
        mf.get_by_role("button", name="발행").last.click()
        time.sleep(5.0)

        print(f"🎉 성공적으로 발행되었습니다! (모드: {'전체공개' if is_public else '비공개'})")
        page.close()
        ctx.close()

if __name__ == "__main__":
    is_pub = "--public" in sys.argv
    publish(is_public=is_pub)
