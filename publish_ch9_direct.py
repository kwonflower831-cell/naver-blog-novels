import ctypes
import json
import os
import re
import subprocess
import sys
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
CH9_PATH = BASE_DIR / "novel-yupum-text" / "ch9-published.txt"
ASIDE_CH9_PATH = Path(r"C:\Users\kwonf\.aside\u\0\memory\agent\novel-yupum-text\ch9-published.txt")
INTRO_PATH = BASE_DIR / "novel-yupum-text" / "intro-published.txt"
ASIDE_INTRO_PATH = Path(r"C:\Users\kwonf\.aside\u\0\memory\agent\novel-yupum-text\intro-published.txt")

raw9 = CH9_PATH.read_text(encoding="utf-8").replace("\r\n", "\n").strip()
parts9 = [p for p in raw9.split("\n\n") if p.strip()]
print(f"Loaded Ch9 parts: {len(parts9)}", flush=True)

def fetch_text(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8", errors="replace")

def get_cat11_items():
    txt = fetch_text("https://blog.naver.com/PostTitleListAsync.naver?blogId=kwonflower58&currentPage=1&categoryNo=11&countPerPage=15")
    matches = re.findall(r'"logNo":"(\d+)","title":"([^"]*)","categoryNo":"(\d+)"', txt)
    return [(m[0], urllib.parse.unquote(m[1].replace("+", " ")), m[2]) for m in matches]

def decode_html_text(s: str) -> str:
    s = re.sub(r"<[^>]+>", "", s)
    s = s.replace("&#x27;", "'").replace("&#39;", "'").replace("&quot;", '"').replace("&amp;", "&").replace("\u200b", "")
    return s.strip()

def is_cdp_available() -> bool:
    try:
        req = urllib.request.Request("http://127.0.0.1:9222/json/version", headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=2) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return "webSocketDebuggerUrl" in data
    except Exception:
        return False

def ensure_chrome_with_cdp():
    if is_cdp_available():
        print("Chrome CDP is already available on 127.0.0.1:9222!", flush=True)
        return

    print("Closing running Chrome to reopen with debugging port 9222...", flush=True)
    subprocess.run("taskkill /F /IM chrome.exe", shell=True, capture_output=True)
    time.sleep(2.5)

    # Make sure chrome is completely closed
    for _ in range(10):
        out = subprocess.check_output('tasklist /fi "IMAGENAME eq chrome.exe"', shell=True, text=True, errors="replace")
        if "chrome.exe" not in out.lower():
            break
        time.sleep(1)

    print("Launching Chrome with --remote-debugging-port=9222 --restore-last-session...", flush=True)
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    if not os.path.exists(chrome_path):
        chrome_path = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"

    subprocess.Popen([
        chrome_path,
        "--remote-debugging-port=9222",
        "--restore-last-session"
    ], creationflags=0x00000008) # DETACHED_PROCESS

    for i in range(20):
        if is_cdp_available():
            print(f"CDP connected successfully on attempt {i+1}!", flush=True)
            time.sleep(2.0)
            return
        time.sleep(0.5)

    raise RuntimeError("Failed to connect to Chrome on CDP 127.0.0.1:9222")

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
    target_frame.get_by_text("나눔명조", exact=True).first.click()
    time.sleep(0.8)

def open_link_input(page, target_frame):
    try:
        link_btn = target_frame.locator(
            'button[data-name="text-link"], button[class*="se-link-toolbar-button"], .se-toolbar-item-link button'
        ).first
        if link_btn.count() > 0 and link_btn.is_visible():
            link_btn.click()
            time.sleep(1.0)
    except Exception:
        pass
    url_inputs = target_frame.locator('input[placeholder="URL을 입력하세요."]')
    for idx in range(url_inputs.count() - 1, -1, -1):
        if url_inputs.nth(idx).is_visible():
            return
    page.mouse.click(674, 121)
    time.sleep(1.2)

def main():
    items = get_cat11_items()
    print("Initial category 11 posts:", [f"{i[0]}:{i[1]}" for i in items[:5]], flush=True)
    existing9 = next((i for i in items if "9장" in i[1]), None)

    ensure_chrome_with_cdp()

    with sync_playwright() as p:
        print("Connecting to Chrome on CDP 127.0.0.1:9222...", flush=True)
        browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        ctx = browser.contexts[0]
        page = ctx.new_page()

        no9 = existing9[0] if existing9 else None
        if not no9:
            print("\n[Chapter 9] Starting publish: 《유품》 9장. 가계부...", flush=True)
            page.goto("https://blog.naver.com/kwonflower58?Redirect=Write&", wait_until="domcontentloaded")
            time.sleep(5.5)

            mf = find_editor_frame(page, timeout_sec=35)
            dismiss_editor_popups(mf)

            # 1. 제목 입력
            mf.locator(".se-documentTitle").first.click()
            page.keyboard.insert_text("《유품》 9장. 가계부")
            time.sleep(0.3)

            # 2. 본문 입력
            mf.locator(".se-component.se-text .se-text-paragraph").first.click()
            for i, para in enumerate(parts9):
                page.keyboard.insert_text(para)
                time.sleep(0.12)
                if i < len(parts9) - 1:
                    page.keyboard.press("Enter")
                    time.sleep(0.12)
                    page.keyboard.press("Enter")
                    time.sleep(0.12)
            time.sleep(0.6)

            # 3. 본문 검증
            dm = mf.locator(".se-component.se-text .se-text-paragraph").evaluate_all(
                "els => els.map(e => e.textContent.replace(/\\u200b/g, ''))"
            )
            nm = [t for t in dm if t.strip() != ""]
            mismatch_count = sum(1 for i, p_text in enumerate(parts9) if i >= len(nm) or nm[i] != p_text)
            print(f"[Chapter 9] DOM: {len(dm)}, nonEmpty: {len(nm)}, expected: {len(parts9)}, mismatch: {mismatch_count}", flush=True)
            if len(nm) != len(parts9) or mismatch_count != 0:
                raise RuntimeError(f"Paragraph mismatch: nonEmpty={len(nm)}, mismatch={mismatch_count}")

            # 4. 글꼴 나눔명조 적용
            mf.locator(".se-component.se-text .se-text-paragraph").nth(2).click()
            page.keyboard.press("Control+A")
            time.sleep(0.3)
            click_font_nanummyeongjo(page, mf)

            # 5. 발행 패널 열기
            mf.get_by_role("button", name="발행").first.click()
            time.sleep(1.5)

            # 6. 카테고리 연재소설 유품 선택
            mf.get_by_role("button", name="카테고리 목록 버튼").first.click()
            time.sleep(0.7)
            mf.get_by_role("button", name="연재소설 유품").first.click()
            time.sleep(0.6)

            # 7. 태그 입력
            tag_box = mf.get_by_role("combobox", name=re.compile(r"^태그"))
            if tag_box.count() > 0:
                tag_box.first.click()
            else:
                mf.locator('input[placeholder*="태그"], [aria-label*="태그"], [id*="tag-input"]').first.click()
            for tg in ["유품", "연재소설", "스릴러", "소설", "유품정리"]:
                page.keyboard.insert_text(tg)
                page.keyboard.press("Enter")
                time.sleep(0.3)

            # 8. 설정 상태 검증
            st = mf.evaluate("""() => ({
                catBtn: [...document.querySelectorAll('button')].map(b => b.textContent.trim()).filter(t => t.startsWith('연재소설') || t === '생활용품 가격비교'),
                checked: [...document.querySelectorAll('input:checked')].map(i => i.id),
                tags: [...document.querySelectorAll('[class*="tag_text"]')].map(e => e.textContent)
            })""")
            print("[Chapter 9] Publish panel state:", st, flush=True)
            if not ("연재소설 유품" in st["catBtn"] and "open_public" in st["checked"] and "set-notice" not in st["checked"]):
                raise RuntimeError(f"Chapter 9 publish panel state wrong: {st}")

            # 9. 최종 발행 클릭
            mf.get_by_role("button", name="발행").last.click()
            time.sleep(5.5)

            # 10. 발행 글 logNo 확인
            for retry in range(10):
                items = get_cat11_items()
                cand = next((i[0] for i in items if "9장" in i[1]), None)
                if cand:
                    no9 = cand
                    break
                time.sleep(2.0)
            if not no9:
                raise RuntimeError("Could not find published 9장 in category 11")
            print(f"[Chapter 9] SUCCESS! logNo = {no9}", flush=True)
        else:
            print(f"9장 already published: {no9}", flush=True)

        # 11. 공지글(소개 및 목차) 갱신
        print("\n[Intro Notice] Updating Table of Contents...", flush=True)
        intro_src = INTRO_PATH.read_text(encoding="utf-8").replace("\r\n", "\n").strip().split("\n\n")
        intro9 = list(intro_src)
        if "9장. 가계부" not in intro9:
            i8 = intro9.index("8장. 예정일")
            intro9.insert(i8 + 1, "9장. 가계부")

        page.goto("https://blog.naver.com/kwonflower58/postupdate?logNo=224468231033", wait_until="domcontentloaded")
        time.sleep(6)

        ef = find_editor_frame(page, timeout_sec=35)
        dismiss_editor_popups(ef)

        bl = ef.locator(".se-component.se-text .se-text-paragraph")
        bl.nth(2).click()
        page.keyboard.press("Control+A")
        page.keyboard.press("Delete")
        time.sleep(0.6)
        bl.first.click()
        for i, para in enumerate(intro9):
            page.keyboard.insert_text(para)
            time.sleep(0.12)
            if i < len(intro9) - 1:
                page.keyboard.press("Enter")
                time.sleep(0.12)
                page.keyboard.press("Enter")
                time.sleep(0.12)
        time.sleep(0.6)

        bl.nth(2).click()
        page.keyboard.press("Control+A")
        time.sleep(0.3)
        click_font_nanummyeongjo(page, ef)

        def add_link(text: str, url: str):
            chap_match = re.match(r"^(\d+)장\.", text)
            chap_num = int(chap_match.group(1)) if chap_match else None
            for attempt in range(5):
                if chap_num and (chap_num >= 6 or attempt >= 1):
                    toc_header = ef.locator(".se-component.se-text .se-text-paragraph", has_text="[목차]").first
                    toc_header.click()
                    time.sleep(0.25)
                    page.keyboard.press("Home")
                    for _ in range(chap_num * 2):
                        page.keyboard.press("ArrowDown")
                        time.sleep(0.12)
                    time.sleep(0.25)
                else:
                    tgt = ef.locator(".se-component.se-text .se-text-paragraph", has_text=text).first
                    tgt.click()
                    time.sleep(0.25)

                page.keyboard.press("Home")
                page.keyboard.press("Shift+End")
                time.sleep(0.4)
                open_link_input(page, ef)

                url_inputs = ef.locator('input[placeholder="URL을 입력하세요."]')
                confirm_btns = ef.locator('button.se-custom-layer-link-apply-button, button[aria-label="링크 입력"], button:has-text("링크 입력")')
                visible_input = None
                for idx in range(url_inputs.count() - 1, -1, -1):
                    cand = url_inputs.nth(idx)
                    if cand.is_visible():
                        visible_input = cand
                        break
                visible_btn = None
                for idx in range(confirm_btns.count() - 1, -1, -1):
                    cand = confirm_btns.nth(idx)
                    if cand.is_visible():
                        visible_btn = cand
                        break

                if visible_input and visible_btn:
                    visible_input.fill(url)
                    time.sleep(0.25)
                    visible_btn.click()
                    time.sleep(1.0)
                    return
                print(f"Retry {attempt + 1} for link: {text}", flush=True)
                page.keyboard.press("Escape")
                time.sleep(0.5)
            raise RuntimeError(f"Failed to add link after retries: {text}")

        BV = "https://blog.naver.com/kwonflower58/"
        link_list = [
            ("▶ 1장부터 읽기", "224468217040"),
            ("1장. 냉장고 뒤", "224468217040"),
            ("2장. 치우는 사람", "224468245875"),
            ("3장. 열쇠 번호", "224468270708"),
            ("4장. 번진 이름", "224468285867"),
            ("5장. 두 번, 쉬고, 두 번", "224468850864"),
            ("6장. 아직", "224468866173"),
            ("7장. 먼지 없는 네모", "224470123011"),
            ("8장. 예정일", "224470196843"),
            ("9장. 가계부", no9),
        ]
        for tx, no in link_list:
            add_link(tx, BV + no)

        ef.get_by_role("button", name="발행").first.click()
        time.sleep(1.5)

        notice_box = ef.locator('#set-notice')
        if notice_box.count() > 0 and not notice_box.first.is_checked():
            notice_box.first.click()
            time.sleep(0.5)

        st_intro = ef.evaluate("""() => ({
            catBtn: [...document.querySelectorAll('button')].map(b => b.textContent.trim()).filter(t => t.startsWith('연재소설')),
            notice: document.querySelector('#set-notice')?.checked,
            tags: [...document.querySelectorAll('[class*="tag_text"]')].map(e => e.textContent)
        })""")
        print("[Intro Notice] Publish panel state:", st_intro, flush=True)
        if not st_intro["notice"] or "연재소설 유품" not in st_intro["catBtn"]:
            raise RuntimeError(f"Intro panel wrong: {st_intro}")

        ef.get_by_role("button", name="발행").last.click()
        time.sleep(5.5)

        intro_text_out = "\n\n".join(intro9) + "\n"
        INTRO_PATH.write_text(intro_text_out, encoding="utf-8")
        if ASIDE_INTRO_PATH.parent.exists():
            ASIDE_INTRO_PATH.write_text(intro_text_out, encoding="utf-8")

        page.close()
        print(f"\n🎉 ALL COMPLETE! 9장 logNo: {no9} 발행 및 공지 갱신 완료!", flush=True)

if __name__ == "__main__":
    main()
