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
CH9_PATH = BASE_DIR / "novel-yupum-text" / "ch9-published.txt"
CH10_PATH = BASE_DIR / "novel-yupum-text" / "ch10-draft.txt"
CH10_PUB_PATH = BASE_DIR / "novel-yupum-text" / "ch10-published.txt"
INTRO_PATH = BASE_DIR / "novel-yupum-text" / "intro-published.txt"
PROFILE_DIR = r"C:\Users\kwonf\.gemini\antigravity\scratch\chrome-naver-profile"

raw9 = CH9_PATH.read_text(encoding="utf-8").replace("\r\n", "\n").strip()
parts9 = [p for p in raw9.split("\n\n") if p.strip()]

raw10 = CH10_PATH.read_text(encoding="utf-8").replace("\r\n", "\n").strip()
parts10 = [p for p in raw10.split("\n\n") if p.strip()]

print(f"Loaded Ch9 parts: {len(parts9)}, Ch10 parts: {len(parts10)}", flush=True)

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

def bring_window_to_top():
    try:
        user32 = ctypes.windll.user32
        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
        def enum_cb(hwnd, lparam):
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
    except Exception as e:
        print("bring_window_to_top note:", e, flush=True)

def find_editor_frame(page, timeout_sec=35):
    for _ in range(timeout_sec * 2):
        for f in page.frames:
            try:
                if f.locator(".se-documentTitle").count() > 0 or f.locator(".se-component.se-text .se-text-paragraph").count() > 0:
                    return f
            except Exception:
                pass
        time.sleep(0.5)
    raise RuntimeError(f"Editor frame not found. URL={page.url}, frames={[f.url for f in page.frames]}")

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

def is_logged_in(ctx, page):
    try:
        all_cookies = ctx.cookies()
        if any(c.get("name") in ("NID_AUT", "NID_SES") for c in all_cookies):
            return True
        for p in ctx.pages:
            u = p.url.lower()
            if "nidlogin" not in u and ("blog.naver.com" in u or "postwrite" in u):
                return True
    except Exception:
        pass
    return False

def publish_chapter(page, chapter_num: int, title: str, paragraphs: list) -> str:
    print(f"\n[Chapter {chapter_num}] Starting publish: {title}...", flush=True)
    page.goto("https://blog.naver.com/kwonflower58?Redirect=Write&", wait_until="domcontentloaded")
    time.sleep(5.5)

    mf = find_editor_frame(page, timeout_sec=35)
    dismiss_editor_popups(mf)

    # 1. 제목 입력
    mf.locator(".se-documentTitle").first.click()
    page.keyboard.insert_text(title)
    time.sleep(0.3)

    # 2. 본문 입력
    mf.locator(".se-component.se-text .se-text-paragraph").first.click()
    for i, para in enumerate(paragraphs):
        page.keyboard.insert_text(para)
        time.sleep(0.12)
        if i < len(paragraphs) - 1:
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
    mismatch_count = sum(1 for i, p_text in enumerate(paragraphs) if i >= len(nm) or nm[i] != p_text)
    print(f"[Chapter {chapter_num}] DOM paragraphs: {len(dm)}, nonEmpty: {len(nm)}, expected: {len(paragraphs)}, mismatch: {mismatch_count}", flush=True)
    if len(nm) != len(paragraphs) or mismatch_count != 0:
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
    print(f"[Chapter {chapter_num}] Publish panel state:", st, flush=True)
    if not ("연재소설 유품" in st["catBtn"] and "open_public" in st["checked"] and "set-notice" not in st["checked"]):
        raise RuntimeError(f"Chapter {chapter_num} publish panel state wrong: {st}")

    # 9. 최종 발행 클릭
    mf.get_by_role("button", name="발행").last.click()
    time.sleep(5.5)

    # 10. 발행 글 logNo 확인
    no = None
    for retry in range(10):
        items = get_cat11_items()
        print(f"[Chapter {chapter_num}] (Attempt {retry+1}) Category 11 posts:", [f"{i[0]}:{i[1]}" for i in items[:5]], flush=True)
        cand = next((i[0] for i in items if f"{chapter_num}장" in i[1]), None)
        if cand:
            no = cand
            break
        time.sleep(2.0)
    if not no:
        raise RuntimeError(f"Could not find published {chapter_num}장 in category 11")
    print(f"[Chapter {chapter_num}] SUCCESS! logNo = {no}", flush=True)
    return no

def update_intro_notice(page, no9: str, no10: str):
    print("\n[Intro Notice] Updating Table of Contents...", flush=True)
    intro_src = INTRO_PATH.read_text(encoding="utf-8").replace("\r\n", "\n").strip().split("\n\n")
    intro = list(intro_src)
    
    if "9장. 가계부" not in intro:
        i8 = intro.index("8장. 예정일")
        intro.insert(i8 + 1, "9장. 가계부")
    if "10장. 대질" not in intro:
        i9 = intro.index("9장. 가계부")
        intro.insert(i9 + 1, "10장. 대질")
        
    print("Intro paragraph count:", len(intro), flush=True)

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
    for i, para in enumerate(intro):
        page.keyboard.insert_text(para)
        time.sleep(0.12)
        if i < len(intro) - 1:
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
        ("10장. 대질", no10),
    ]
    for tx, no in link_list:
        add_link(tx, BV + no)

    lk_intro = bl.evaluate_all(
        "els => els.flatMap(e => [...e.querySelectorAll('.se-link, a')].map(a => [a.textContent.trim(), a.getAttribute('data-href') || a.getAttribute('href')]))"
    )
    print("Intro links applied count:", len(lk_intro), flush=True)

    ef.get_by_role("button", name="발행").first.click()
    time.sleep(1.5)

    st_intro = ef.evaluate("""() => ({
        catBtn: [...document.querySelectorAll('button')].map(b => b.textContent.trim()).filter(t => t.startsWith('연재소설')),
        notice: document.querySelector('#set-notice')?.checked,
        tags: [...document.querySelectorAll('[class*="tag_text"]')].map(e => e.textContent)
    })""")
    print("Intro publish panel state:", st_intro, flush=True)
    if not st_intro["notice"] or "연재소설 유품" not in st_intro["catBtn"]:
        raise RuntimeError(f"Intro panel wrong: {st_intro}")

    ef.get_by_role("button", name="발행").last.click()
    time.sleep(5.5)

    intro_text_out = "\n\n".join(intro) + "\n"
    INTRO_PATH.write_text(intro_text_out, encoding="utf-8")
    print(f"[Intro Notice] SUCCESS! Updated notice with 9장 ({no9}) and 10장 ({no10})", flush=True)

def main():
    items = get_cat11_items()
    print("Initial category 11 posts:", [i[0] for i in items], flush=True)
    existing9 = next((i for i in items if "9장" in i[1]), None)
    existing10 = next((i for i in items if "10장" in i[1]), None)

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
            print("Navigating to Naver Login page...", flush=True)
            page.goto("https://nid.naver.com/nidlogin.login?url=https%3A%2F%2Fblog.naver.com%2Fkwonflower58%3FRedirect%3DWrite%26", wait_until="domcontentloaded")
            page.bring_to_front()
            bring_window_to_top()
            
            def show_popup():
                try:
                    ctypes.windll.user32.MessageBoxW(
                        0,
                        "곧 화면에 표시되는 [새 크롬 창]에서 네이버 로그인을 1회 완료해 주세요.\n\n"
                        "※ 기존에 열려 있던 크롬이 아닌, 화면 상단에 배너가 떠 있는 '새 창'에서 로그인하셔야 자동 감지됩니다.\n"
                        "(스마트폰 네이버 앱의 QR코드 로그인도 가능합니다)",
                        "《유품》 9장·10장 자동 발행 대기 안내",
                        0x40 | 0x10000 # MB_ICONINFORMATION | MB_SETFOREGROUND
                    )
                except Exception:
                    pass
            threading.Thread(target=show_popup, daemon=True).start()
            try:
                page.evaluate("""() => {
                    const keep = document.querySelector('#keep');
                    if (keep && !keep.checked) keep.click();
                    if (!document.getElementById('yupum-helper-banner')) {
                        const b = document.createElement('div');
                        b.id = 'yupum-helper-banner';
                        b.style.cssText = 'position:fixed;top:12px;left:50%;transform:translateX(-50%);z-index:9999999;background:#ffffff;border:3px solid #2db400;border-radius:12px;box-shadow:0 8px 24px rgba(0,0,0,0.3);padding:14px 28px;text-align:center;font-family:sans-serif;pointer-events:none;';
                        b.innerHTML = '<div style=\"font-size:18px;font-weight:bold;color:#2db400;margin-bottom:6px;\">📢 [《유품》 9장·10장 자동 발행 대기]</div><div style=\"font-size:15px;color:#222;\">이 창에서 네이버 <b>로그인</b>을 하시면 즉시 <b>9장, 10장 발행 및 목차 갱신</b>이 전자동으로 시작됩니다!</div>';
                        document.body.prepend(b);
                    }
                }""")
            except Exception:
                pass

            print("WAITING_FOR_LOGIN: Polling for login...", flush=True)
            logged_in = False
            for sec in range(900):
                if is_logged_in(ctx, page):
                    print("Naver login confirmed in automation window!", flush=True)
                    logged_in = True
                    time.sleep(2.0)
                    break
                time.sleep(1)

            if not logged_in:
                raise RuntimeError("Timed out waiting for Naver login.")

        no9 = existing9[0] if existing9 else None
        if not no9:
            no9 = publish_chapter(page, 9, "《유품》 9장. 가계부", parts9)
        else:
            print(f"9장 already published: {no9}", flush=True)

        no10 = existing10[0] if existing10 else None
        if not no10:
            no10 = publish_chapter(page, 10, "《유품》 10장. 대질", parts10)
            CH10_PUB_PATH.write_text(raw10 + "\n", encoding="utf-8")
        else:
            print(f"10장 already published: {no10}", flush=True)

        update_intro_notice(page, no9, no10)

        page.close()
        ctx.close()
        print(f"\n🎉 ALL COMPLETE! 9장: {no9}, 10장: {no10}", flush=True)

if __name__ == "__main__":
    main()
