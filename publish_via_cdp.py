import re
import sys
import time
import subprocess
import urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

CHROME_EXE = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
CH1_PATH = Path(r"D:\사용자\storyops\novels\chronos_arcana\chapters\ch1-draft.txt")

def is_cdp_ready():
    try:
        with urllib.request.urlopen("http://localhost:9222/json/version", timeout=1) as resp:
            return resp.status == 200
    except Exception:
        return False

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
    print("=" * 65)
    print("🚀 [사용자 크롬 글쓰기 창 직접 연결(CDP) 전자동 발행 엔진]")
    print("=" * 65)

    # 1. 크롬을 9222 포트로 실행 (이미 실행되어 있지 않다면)
    if not is_cdp_ready():
        print("1. 사용자의 실제 크롬 브라우저(글쓰기 창) 실행 중...")
        cmd = [
            CHROME_EXE,
            "--remote-debugging-port=9222",
            "https://blog.naver.com/kwonflower58?Redirect=Write&"
        ]
        subprocess.Popen(cmd)
        
        # 포트 리슨 대기
        for _ in range(20):
            if is_cdp_ready():
                print("✔ 크롬 CDP 포트(9222) 연결 준비 완료!")
                break
            time.sleep(0.5)

    # 2. 원고 준비
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

    # 3. Playwright CDP 연결
    print("2. 열린 브라우저의 스마트에디터 창에 에이전트 자동 연결 중...")
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0]
        
        # 글쓰기 페이지 찾기
        page = None
        for pg in context.pages:
            if "blog.naver.com" in pg.url or "postwrite" in pg.url:
                page = pg
                break
        if not page:
            page = context.pages[0]

        print(f"✔ 페이지 연결 성공: {page.url}")
        time.sleep(3.0)

        # 4. 에디터 프레임 탐색
        print("3. 에디터 프레임 탐색 및 팝업 정리 중...")
        mf = find_editor_frame(page, timeout_sec=40)
        dismiss_editor_popups(mf)

        # 5. 제목 자동 입력
        print(f"4. ✍️ 제목 자동 타이핑 중: {title}")
        title_box = mf.locator(".se-documentTitle .se-ff-nanumgothic, .se-documentTitle input, .se-documentTitle [contenteditable='true']").first
        title_box.click()
        time.sleep(0.4)
        page.keyboard.insert_text(title)
        time.sleep(0.4)

        # 6. 본문 자동 입력
        print(f"5. ✍️ 본문 {len(paragraphs)}개 문단 자동 작성 중...")
        bl = mf.locator(".se-component.se-text .se-text-paragraph").first
        bl.click()
        time.sleep(0.4)

        for i, para in enumerate(paragraphs):
            page.keyboard.insert_text(para)
            time.sleep(0.02)
            if i < len(paragraphs) - 1:
                page.keyboard.press("Enter")
                time.sleep(0.02)
                page.keyboard.press("Enter")
                time.sleep(0.02)

        time.sleep(1.0)
        print("✔ 본문 작성 완료!")

        # 7. 우측 상단 [발행] 설정 열기
        print("6. ⚙️ [발행] 설정 패널 여는 중...")
        mf.get_by_role("button", name="발행").first.click()
        time.sleep(2.0)

        # 8. 태그 자동 입력
        if tags:
            print(f"7. 🏷️ 태그 {len(tags)}개 자동 입력 중...")
            tag_box = mf.get_by_role("combobox", name=re.compile(r"^태그"))
            if tag_box.count() > 0:
                tag_box.first.click()
            else:
                mf.locator('input[placeholder*="태그"], [aria-label*="태그"], [id*="tag-input"]').first.click()

            for tg in tags[:10]:
                page.keyboard.insert_text(tg)
                page.keyboard.press("Enter")
                time.sleep(0.12)
            print("✔ 태그 입력 완료!")

        # 9. 전체공개 확인
        try:
            mf.locator('label[for="open_all"], input#open_all, label:has-text("전체공개")').first.click()
            time.sleep(0.4)
        except Exception:
            pass

        # 10. 최종 [발행] 버튼 클릭
        print("8. 🚀 최종 [발행] 버튼 클릭 중...")
        mf.get_by_role("button", name="발행").last.click()
        time.sleep(5.0)

        print("\n" + "=" * 65)
        print("🎉 [100% 무인 발행 대성공!] 《크로노스 아르카나》 1장이 네이버 블로그에 발행되었습니다!")
        print("=" * 65 + "\n")

if __name__ == "__main__":
    main()
